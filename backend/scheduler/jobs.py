"""
スケジューラーのジョブ定義
Cloud Scheduler → POST /internal/jobs/{job_name} → APScheduler が即時実行
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from database import SessionLocal
from models import SaleEvent
from services.rss_parser import collect_all_rss
from services.gemini import detect_flash_sales
from services.cache import cleanup_expired_cache

logger = logging.getLogger(__name__)


def _get_db() -> Session:
    return SessionLocal()


async def job_collect_rss():
    """JAL / ANA / LCC の RSS フィードを収集して DB に保存する。"""
    db = _get_db()
    try:
        entries = await collect_all_rss()
        saved = 0
        for entry in entries:
            source = entry.get("source")
            ext_id = entry.get("external_id")
            if not ext_id:
                continue
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
        logger.info("RSS collect: %d new events saved", saved)
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
