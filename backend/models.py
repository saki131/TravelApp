from sqlalchemy import (
    Column, String, Text, Integer, SmallInteger, Boolean, Date,
    Numeric, CHAR, ForeignKey, UniqueConstraint, DateTime, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid

# PostgreSQL の UUID 型を使えなぁE��墁E��けに String で代替
class _UUID(String):
    def __init__(self):
        super().__init__(36)

def _uuid_default():
    return str(uuid.uuid4())


class Airport(Base):
    __tablename__ = "airports"

    iata_code    = Column(CHAR(3), primary_key=True)
    icao_code    = Column(CHAR(4))
    name_ja      = Column(String(100), nullable=False)
    name_en      = Column(String(100), nullable=False)
    city_ja      = Column(String(100))
    city_en      = Column(String(100))
    country_code = Column(CHAR(2), nullable=False)
    country_ja   = Column(String(100))
    latitude     = Column(Numeric(9, 6))
    longitude    = Column(Numeric(9, 6))
    timezone     = Column(String(50))
    is_active    = Column(Boolean, nullable=False, default=True)
    updated_at   = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class FlightSearchCache(Base):
    __tablename__ = "flight_search_cache"

    id                = Column(_UUID(), primary_key=True, default=_uuid_default)
    search_query_hash = Column(String(64), nullable=False, unique=True)
    origin_iata       = Column(CHAR(3), ForeignKey("airports.iata_code"), nullable=False)
    destination_iata  = Column(CHAR(3), ForeignKey("airports.iata_code"), nullable=False)
    departure_date    = Column(Date, nullable=False)
    return_date       = Column(Date)
    cabin_class       = Column(String(20), nullable=False, default="ECONOMY")
    adults            = Column(SmallInteger, nullable=False, default=1)
    nonstop_only      = Column(Boolean, nullable=False, default=False)
    result_json       = Column(JSON, nullable=False)
    source_api        = Column(String(20), nullable=False)
    result_count      = Column(SmallInteger)
    cached_at         = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at        = Column(DateTime(timezone=True), nullable=False)


class PriceCalendarCache(Base):
    __tablename__ = "price_calendar_cache"

    id               = Column(_UUID(), primary_key=True, default=_uuid_default)
    origin_iata      = Column(CHAR(3), ForeignKey("airports.iata_code"), nullable=False)
    destination_iata = Column(CHAR(3), ForeignKey("airports.iata_code"), nullable=False)
    travel_date      = Column(Date, nullable=False)
    price_jpy        = Column(Integer)
    source_api       = Column(String(20))
    cached_at        = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at       = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("origin_iata", "destination_iata", "travel_date"),
    )


class InspireCache(Base):
    __tablename__ = "inspire_cache"

    id                  = Column(_UUID(), primary_key=True, default=_uuid_default)
    search_query_hash   = Column(String(64), nullable=False, unique=True)
    origin_iata         = Column(CHAR(3), ForeignKey("airports.iata_code"), nullable=False)
    departure_date_from = Column(Date, nullable=False)
    departure_date_to   = Column(Date, nullable=False)
    max_price_jpy       = Column(Integer)
    result_json         = Column(JSON, nullable=False)
    cached_at           = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at          = Column(DateTime(timezone=True), nullable=False)


class SaleEvent(Base):
    __tablename__ = "sale_events"

    id                  = Column(_UUID(), primary_key=True, default=_uuid_default)
    category            = Column(String(20), nullable=False)   # flight | hotel | package
    title               = Column(String(200), nullable=False)
    description         = Column(Text)
    sale_start          = Column(DateTime(timezone=True))
    sale_end            = Column(DateTime(timezone=True))
    travel_start        = Column(Date)
    travel_end          = Column(Date)
    discount_rate       = Column(Numeric(5, 2))
    min_price_jpy       = Column(Integer)
    target_routes       = Column(JSON)       # [{"origin":"HND","destination":"OKA"}]
    target_destinations = Column(JSON)       # ["OKA","CTS"]
    coupon_code         = Column(String(50))
    booking_url         = Column(Text)
    source              = Column(String(50), nullable=False)
    source_url          = Column(Text)
    is_verified         = Column(Boolean, nullable=False, default=False)
    external_id         = Column(String(200))
    created_at          = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("source", "external_id"),
    )


class Favorite(Base):
    __tablename__ = "favorites"

    id         = Column(_UUID(), primary_key=True, default=_uuid_default)
    type       = Column(String(20), nullable=False)  # flight_route | hotel
    label      = Column(String(100))
    params     = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    alerts = relationship("PriceAlert", back_populates="favorite", cascade="all, delete-orphan")


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id                     = Column(_UUID(), primary_key=True, default=_uuid_default)
    favorite_id            = Column(_UUID(), ForeignKey("favorites.id", ondelete="CASCADE"), nullable=False)
    target_price_jpy       = Column(Integer, nullable=False)
    last_checked_price_jpy = Column(Integer)
    last_notified_at       = Column(DateTime(timezone=True))
    notify_method          = Column(String(20), nullable=False, default="push")
    is_active              = Column(Boolean, nullable=False, default=True)
    created_at             = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at             = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    favorite = relationship("Favorite", back_populates="alerts")


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id           = Column(_UUID(), primary_key=True, default=_uuid_default)
    endpoint     = Column(Text, unique=True, nullable=False)
    p256dh       = Column(Text, nullable=False)
    auth         = Column(Text, nullable=False)
    user_agent   = Column(String(300))
    created_at   = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_used_at = Column(DateTime(timezone=True))
