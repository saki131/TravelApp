"""
DB キャッシュユーティリティ（Redis 不使用）
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import json

from sqlalchemy.orm import Session
from models import FlightSearchCache, PriceCalendarCache, InspireCache


# -----------------------------------------------------------------------
# フライト検索キャッシュ（TTL: 30分）
# -----------------------------------------------------------------------
FLIGHT_CACHE_TTL = timedelta(minutes=30)


def get_flight_cache(db: Session, query_hash: str) -> Optional[dict]:
    row = db.query(FlightSearchCache).filter(
        FlightSearchCache.search_query_hash == query_hash,
        FlightSearchCache.expires_at > datetime.now(timezone.utc),
    ).first()
    if row:
        return row.result_json
    return None


def set_flight_cache(db: Session, query_hash: str, result: dict, **meta) -> None:
    now = datetime.now(timezone.utc)
    # 既存レコードを削除してから挿入（upsert）
    db.query(FlightSearchCache).filter(
        FlightSearchCache.search_query_hash == query_hash
    ).delete()
    row = FlightSearchCache(
        search_query_hash=query_hash,
        result_json=result,
        source_api=meta.get("source_api", "amadeus"),
        cached_at=now,
        expires_at=now + FLIGHT_CACHE_TTL,
        **{k: v for k, v in meta.items() if k != "source_api"},
    )
    db.add(row)
    db.commit()


# -----------------------------------------------------------------------
# 価格カレンダーキャッシュ（TTL: 24時間）
# -----------------------------------------------------------------------
CALENDAR_CACHE_TTL = timedelta(hours=24)


def get_calendar_cache(db: Session, origin: str, destination: str, travel_date) -> Optional[int]:
    row = db.query(PriceCalendarCache).filter(
        PriceCalendarCache.origin_iata == origin,
        PriceCalendarCache.destination_iata == destination,
        PriceCalendarCache.travel_date == travel_date,
        PriceCalendarCache.expires_at > datetime.now(timezone.utc),
    ).first()
    if row:
        return row.price_jpy
    return None


def set_calendar_cache(db: Session, origin: str, destination: str, prices: list[dict]) -> None:
    """prices: [{"date": date_obj, "price_jpy": int}]"""
    now = datetime.now(timezone.utc)
    for item in prices:
        travel_date = item["date"]
        # 既存削除
        db.query(PriceCalendarCache).filter(
            PriceCalendarCache.origin_iata == origin,
            PriceCalendarCache.destination_iata == destination,
            PriceCalendarCache.travel_date == travel_date,
        ).delete()
        row = PriceCalendarCache(
            origin_iata=origin,
            destination_iata=destination,
            travel_date=travel_date,
            price_jpy=item.get("price_jpy"),
            source_api="amadeus",
            cached_at=now,
            expires_at=now + CALENDAR_CACHE_TTL,
        )
        db.add(row)
    db.commit()


# -----------------------------------------------------------------------
# インスパイアキャッシュ（TTL: 6時間）
# -----------------------------------------------------------------------
INSPIRE_CACHE_TTL = timedelta(hours=6)


def get_inspire_cache(db: Session, query_hash: str) -> Optional[dict]:
    row = db.query(InspireCache).filter(
        InspireCache.search_query_hash == query_hash,
        InspireCache.expires_at > datetime.now(timezone.utc),
    ).first()
    if row:
        return row.result_json
    return None


def set_inspire_cache(db: Session, query_hash: str, result: dict, **meta) -> None:
    now = datetime.now(timezone.utc)
    db.query(InspireCache).filter(
        InspireCache.search_query_hash == query_hash
    ).delete()
    row = InspireCache(
        search_query_hash=query_hash,
        result_json=result,
        cached_at=now,
        expires_at=now + INSPIRE_CACHE_TTL,
        **meta,
    )
    db.add(row)
    db.commit()


# -----------------------------------------------------------------------
# キャッシュクリーンアップ（毎日 0時に実行）
# -----------------------------------------------------------------------
def cleanup_expired_cache(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    flight_del = db.query(FlightSearchCache).filter(FlightSearchCache.expires_at < now).delete()
    cal_del    = db.query(PriceCalendarCache).filter(PriceCalendarCache.expires_at < now).delete()
    ins_del    = db.query(InspireCache).filter(InspireCache.expires_at < now).delete()
    db.commit()
    return {"flight": flight_del, "calendar": cal_del, "inspire": ins_del}
