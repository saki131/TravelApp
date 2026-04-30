from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime
import uuid


class FavoriteCreate(BaseModel):
    type: str           # flight_route | hotel
    label: Optional[str] = None
    params: Any         # JSON


class FavoriteOut(BaseModel):
    id: uuid.UUID
    type: str
    label: Optional[str] = None
    params: Any
    created_at: datetime

    class Config:
        from_attributes = True


class PriceAlertCreate(BaseModel):
    favorite_id: uuid.UUID
    target_price_jpy: int


class PriceAlertOut(BaseModel):
    id: uuid.UUID
    favorite_id: uuid.UUID
    target_price_jpy: int
    last_checked_price_jpy: Optional[int] = None
    last_notified_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: Optional[str] = None


class PushSubscriptionOut(BaseModel):
    id: uuid.UUID
    endpoint: str
    created_at: datetime

    class Config:
        from_attributes = True
