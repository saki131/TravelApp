from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date, datetime
import uuid


class SaleEventOut(BaseModel):
    id: uuid.UUID
    category: str
    title: str
    description: Optional[str] = None
    sale_start: Optional[datetime] = None
    sale_end: Optional[datetime] = None
    travel_start: Optional[date] = None
    travel_end: Optional[date] = None
    discount_rate: Optional[float] = None
    min_price_jpy: Optional[int] = None
    target_routes: Optional[Any] = None
    target_destinations: Optional[Any] = None
    coupon_code: Optional[str] = None
    booking_url: Optional[str] = None
    source: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SaleListResponse(BaseModel):
    total: int
    items: List[SaleEventOut]
