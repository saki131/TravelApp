"""
スケジューラーのジョブ定義
Cloud Scheduler → POST /internal/jobs/{job_name} → APScheduler が即時実行
"""
import hashlib
import logging
import re
from datetime import datetime, timezone, date as date_type

import httpx
from sqlalchemy.orm import Session
from database import SessionLocal
from models import SaleEvent
from services.gemini import detect_flash_sales
from services.cache import cleanup_expired_cache
from config import settings

logger = logging.getLogger(__name__)

# SerpApi で検索するセール情報クエリ
_SALE_QUERIES = [
    ("peach",        "ピーチ セール タイムセール 格安航空券"),
    ("jetstar",      "ジェットスター セール タイムセール 格安航空券"),
    ("spring_japan", "スプリングジャパン セール 格安航空券"),
    ("jal",          "JAL 特割 タイムセール 格安航空券"),
    ("ana",          "ANA SUPER VALUE タイムセール"),
]
_OFFICIAL_DOMAINS = {
    "peach":        ["flypeach.com"],
    "jetstar":      ["jetstar.com"],
    "spring_japan": ["springjapan.com", "spring-japan.co.jp"],
    "jal":          ["jal.co.jp"],
    "ana":          ["ana.co.jp"],
}

# 搭乗・旅行期間を示すキーワード
_TRAVEL_KW = ['搭乗', '旅行', '出発', '利用', 'travel']
# 予約期間を示すキーワード
_BOOKING_KW = ['予約', '購入', '販売', 'セール', 'タイムセール', 'sale', '申込', 'booking']


def _infer_year(m: int, d: int, now: datetime) -> int:
    """6ヶ月以内の過去日・未来日に最も近い年を返す。"""
    for year in [now.year, now.year + 1]:
        try:
            dt = datetime(year, m, d, tzinfo=timezone.utc)
            if dt < now and (now - dt).days > 180:
                continue
            return year
        except ValueError:
            pass
    return now.year


def _extract_dates(text: str) -> dict:
    """snippet テキストから sale_start / sale_end / travel_start / travel_end を抽出する。"""
    now = datetime.now(timezone.utc)
    result: dict = {}

    def parse_dt(mo: str, dy: str) -> datetime | None:
        try:
            m, d = int(mo), int(dy)
            if not (1 <= m <= 12 and 1 <= d <= 31):
                return None
            return datetime(_infer_year(m, d, now), m, d, tzinfo=timezone.utc)
        except (ValueError, OverflowError):
            return None

    def is_travel(pos: int) -> bool:
        ctx = text[max(0, pos - 15):pos + 15]
        return any(kw in ctx for kw in _TRAVEL_KW)

    # パターン1: 範囲 M/D〜M/D または M月D日〜M月D日
    for m in re.finditer(r'(\d{1,2})[/月](\d{1,2})日?\s*[〞~～\-]　?\s*(\d{1,2})[/月](\d{1,2})', text):
        s, e = parse_dt(m.group(1), m.group(2)), parse_dt(m.group(3), m.group(4))
        if s and e:
            if is_travel(m.start()):
                result.setdefault('travel_start', s.date())
                result.setdefault('travel_end', e.date())
            else:
                result.setdefault('sale_start', s)
                result.setdefault('sale_end', e)

    # パターン2: 〜M/Dまで (終了のみ)
    for m in re.finditer(r'[〞~～]?\s*(\d{1,2})[/月](\d{1,2})日?\s*(?:まで|迄)', text):
        e = parse_dt(m.group(1), m.group(2))
        if e:
            if is_travel(m.start()):
                result.setdefault('travel_end', e.date())
            else:
                result.setdefault('sale_end', e)

    # パターン3: 単一日付 M/D または M月D日 (未分類 → sale_end)
    if 'sale_end' not in result:
        m = re.search(r'(\d{1,2})[/月](\d{1,2})', text)
        if m:
            e = parse_dt(m.group(1), m.group(2))
            if e:
                result['sale_end'] = e

    return result


def _get_db() -> Session:
    return SessionLocal()


async def _search_sale(source: str, query: str) -> list[dict]:
    params = {
        "engine": "google",
        "q": query,
        "hl": "ja",
        "gl": "jp",
        "num": 10,
        "api_key": settings.SERPAPI_KEY,
    }
    async with httpx.AsyncClient(timeout=20) as c:
        resp = await c.get("https://serpapi.com/search", params=params)
        raw = resp.json()

    results = []
    official_domains = _OFFICIAL_DOMAINS.get(source, [])
    for r in raw.get("organic_results", []):
        title = r.get("title", "").strip()
        link = r.get("link", "").strip()
        snippet = r.get("snippet", "").strip()
        if not title or not link:
            continue
        is_official = any(d in link for d in official_domains)

        price_match = re.search(r"[¥￥]?(\d{1,3}(?:,\d{3})*|\d{3,6})\s*円", snippet)
        min_price = None
        if price_match:
            try:
                min_price = int(price_match.group(1).replace(",", ""))
            except Exception:
                pass

        # 日付抽出（強化版）
        dates = _extract_dates(snippet)

        results.append({
            "category": "flight",
            "title": title[:200],
            "description": snippet[:500] if snippet else None,
            "sale_start": dates.get("sale_start"),
            "sale_end":   dates.get("sale_end"),
            "travel_start": dates.get("travel_start"),
            "travel_end":   dates.get("travel_end"),
            "min_price_jpy": min_price,
            "booking_url": link,
            "source": source,
            "source_url": link,
            "is_verified": is_official,
            "external_id": hashlib.md5(link.encode()).hexdigest(),
        })

    results.sort(key=lambda x: (0 if x["is_verified"] else 1))
    return results[:3]


async def job_collect_rss():
    """SerpApi Google検索で各社のセール情報を収集して DB に保存する（旧RSS収集の代替）。"""
    if not settings.SERPAPI_KEY:
        logger.warning("SERPAPI_KEY が未設定のためセール収集をスキップ")
        return
    db = _get_db()
    try:
        all_entries = []
        for source, query in _SALE_QUERIES:
            try:
                entries = await _search_sale(source, query)
                all_entries.extend(entries)
                logger.info("SerpApi sale collect [%s]: %d件", source, len(entries))
            except Exception as e:
                logger.warning("SerpApi sale collect error [%s]: %s", source, e)

        saved = 0
        for entry in all_entries:
            source = entry.get("source")
            ext_id = entry.get("external_id")
            if not ext_id:
                continue
            exists = db.query(SaleEvent).filter(
                SaleEvent.source == source,
                SaleEvent.external_id == ext_id,
            ).first()
            if exists:
                # タイトル・説明を最新に更新
                exists.title = entry["title"]
                exists.description = entry.get("description")
                exists.sale_start  = entry.get("sale_start")
                exists.sale_end    = entry.get("sale_end")
                exists.travel_start = entry.get("travel_start")
                exists.travel_end   = entry.get("travel_end")
                exists.min_price_jpy = entry.get("min_price_jpy")
            else:
                event = SaleEvent(**{k: v for k, v in entry.items() if hasattr(SaleEvent, k)})
                db.add(event)
                saved += 1
        db.commit()
        logger.info("SerpApi sale collect: %d new events saved", saved)
    except Exception as e:
        logger.error("job_collect_rss error: %s", e)
        db.rollback()
    finally:
        db.close()


async def job_gemini_grounding():
    """Gemini Google Search グラウンディングでフラッシュセールを検知する。"""
    db = _get_db()
    try:
        sales = await detect_flash_sales()
        saved = 0
        for s in sales:
            title = s.get("title", "")[:200]
            source = f"gemini_{s.get('source', 'unknown')[:30]}"
            ext_id = f"{source}_{hash(title)}"

            exists = db.query(SaleEvent).filter(
                SaleEvent.source == source,
                SaleEvent.external_id == str(ext_id),
            ).first()
            if exists:
                continue

            event = SaleEvent(
                category=s.get("category", "flight"),
                title=title,
                description=s.get("description"),
                sale_end=_parse_date(s.get("sale_end")),
                travel_start=_parse_date(s.get("travel_start")),
                travel_end=_parse_date(s.get("travel_end")),
                min_price_jpy=s.get("min_price_jpy"),
                discount_rate=s.get("discount_rate"),
                target_routes=s.get("target_routes"),
                booking_url=s.get("booking_url"),
                coupon_code=s.get("coupon_code"),
                source=source,
                is_verified=False,
                external_id=str(ext_id),
            )
            db.add(event)
            saved += 1
        db.commit()
        logger.info("Gemini grounding: %d new events saved", saved)
    except Exception as e:
        logger.error("job_gemini_grounding error: %s", e)
        db.rollback()
    finally:
        db.close()


def job_cleanup():
    """期限切れキャッシュ・古いセールイベントを削除する。"""
    db = _get_db()
    try:
        result = cleanup_expired_cache(db)
        logger.info("Cache cleanup: %s", result)

        # 終了から60日以上経ったセールイベントを削除
        from sqlalchemy import text
        db.execute(text(
            "DELETE FROM sale_events WHERE sale_end < NOW() - interval '60 days'"
        ))
        db.commit()
    except Exception as e:
        logger.error("job_cleanup error: %s", e)
        db.rollback()
    finally:
        db.close()


def _parse_date(val):
    if not val:
        return None
    try:
        return datetime.fromisoformat(val).date()
    except Exception:
        return None
