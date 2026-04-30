"""SerpApi Google検索で実際のセール情報を取得・保存するスクリプト"""
import asyncio
import hashlib
import os
import re
import sys
from datetime import datetime, timezone, date as date_type

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

import httpx

SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

_TRAVEL_KW = ['搭乗', '旅行', '出発', '利用', 'travel']

def _infer_year(m: int, d: int, now: datetime) -> int:
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
    for m in re.finditer(r'(\d{1,2})[/月](\d{1,2})日?\s*[〜~～\-]　?\s*(\d{1,2})[/月](\d{1,2})', text):
        s, e = parse_dt(m.group(1), m.group(2)), parse_dt(m.group(3), m.group(4))
        if s and e:
            if is_travel(m.start()):
                result.setdefault('travel_start', s.date())
                result.setdefault('travel_end', e.date())
            else:
                result.setdefault('sale_start', s)
                result.setdefault('sale_end', e)

    # パターン2: 〜M/Dまで (終了のみ)
    for m in re.finditer(r'[〜~～]?\s*(\d{1,2})[/月](\d{1,2})日?\s*(?:まで|迄)', text):
        e = parse_dt(m.group(1), m.group(2))
        if e:
            if is_travel(m.start()):
                result.setdefault('travel_end', e.date())
            else:
                result.setdefault('sale_end', e)

    # パターン3: 単一日付 M/D (未分類 → sale_end)
    if 'sale_end' not in result:
        m = re.search(r'(\d{1,2})[/月](\d{1,2})', text)
        if m:
            e = parse_dt(m.group(1), m.group(2))
            if e:
                result['sale_end'] = e

    return result

# セール検索クエリ一覧
SALE_QUERIES = [
    ("peach",         "ピーチ セール タイムセール 2026年5月 格安航空券"),
    ("jetstar",       "ジェットスター セール タイムセール 2026年5月"),
    ("spring_japan",  "スプリングジャパン セール 2026年5月"),
    ("jal",           "JAL 特割 先得 タイムセール 2026年5月"),
    ("ana",           "ANA スーパーバリュー セール 2026年5月"),
]

# ソース別の公式ドメイン（これらのリンクのみ採用）
OFFICIAL_DOMAINS = {
    "peach":        ["flypeach.com"],
    "jetstar":      ["jetstar.com"],
    "spring_japan": ["springjapan.com", "spring-japan.co.jp"],
    "jal":          ["jal.co.jp", "jal.com"],
    "ana":          ["ana.co.jp", "ana.com"],
}


async def search_sales(source: str, query: str) -> list[dict]:
    params = {
        "engine": "google",
        "q": query,
        "hl": "ja",
        "gl": "jp",
        "num": 10,
        "api_key": SERPAPI_KEY,
    }
    async with httpx.AsyncClient(timeout=20) as c:
        resp = await c.get("https://serpapi.com/search", params=params)
        raw = resp.json()

    organic = raw.get("organic_results", [])
    results = []
    official_domains = OFFICIAL_DOMAINS.get(source, [])

    for r in organic:
        title = r.get("title", "").strip()
        link = r.get("link", "").strip()
        snippet = r.get("snippet", "").strip()

        if not title or not link:
            continue

        # 公式サイト優先（公式ドメイン以外も採用するが is_verified=False）
        is_official = any(d in link for d in official_domains)

        # 価格の抽出（スニペットから）
        price_match = re.search(r"[¥￥]?(\d{1,3}(?:,\d{3})*|\d{3,6})\s*円", snippet)
        min_price = None
        if price_match:
            try:
                min_price = int(price_match.group(1).replace(",", ""))
            except Exception:
                pass

        # 日付抽出（強化版）
        dates = _extract_dates(snippet)

        ext_id = hashlib.md5(link.encode()).hexdigest()
        results.append({
            "category": "flight",
            "title": title[:200],
            "description": snippet[:500] if snippet else None,
            "sale_start":   dates.get("sale_start"),
            "sale_end":     dates.get("sale_end"),
            "travel_start": dates.get("travel_start"),
            "travel_end":   dates.get("travel_end"),
            "min_price_jpy": min_price,
            "booking_url": link,
            "source": source,
            "source_url": link,
            "is_verified": is_official,
            "external_id": ext_id,
        })

    # 公式サイトを優先して上位に
    results.sort(key=lambda x: (0 if x["is_verified"] else 1))
    return results[:3]  # 各ソース最大3件


async def main():
    if not SERPAPI_KEY:
        print("ERROR: SERPAPI_KEY が未設定")
        return

    all_entries = []
    for source, query in SALE_QUERIES:
        try:
            entries = await search_sales(source, query)
            print(f"  {source}: {len(entries)} 件")
            for e in entries:
                print(f"    [{e['is_verified'] and '公式' or '参考'}] {e['title'][:60]}")
                print(f"      {e['booking_url'][:70]}")
            all_entries.extend(entries)
        except Exception as ex:
            print(f"  {source}: ERROR {ex}")

    print(f"\n合計 {len(all_entries)} 件取得")

    if not all_entries:
        print("取得できませんでした")
        return

    # サンプルデータ（seed_sales.py で挿入したもの）を削除して差し替え
    from database import SessionLocal
    from models import SaleEvent

    db = SessionLocal()
    # 既存サンプルを削除（source が seed_sales.py で使ったもの）
    sample_sources = ["spring_japan", "jetstar", "peach", "ana", "rakuten_travel", "jtb", "jal"]
    deleted = db.query(SaleEvent).filter(SaleEvent.source.in_(sample_sources)).delete(synchronize_session=False)
    db.commit()
    print(f"\n古いサンプルデータ {deleted} 件削除")

    # 新規挿入
    saved = 0
    for entry in all_entries:
        ext_id = entry.get("external_id")
        source = entry.get("source")
        exists = db.query(SaleEvent).filter(
            SaleEvent.source == source,
            SaleEvent.external_id == ext_id,
        ).first()
        if exists:
            continue
        event = SaleEvent(**{k: v for k, v in entry.items() if hasattr(SaleEvent, k)})
        db.add(event)
        saved += 1

    db.commit()
    db.close()
    print(f"新規 {saved} 件保存")


if __name__ == "__main__":
    asyncio.run(main())
