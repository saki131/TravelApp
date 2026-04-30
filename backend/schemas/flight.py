from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class FlightSearchRequest(BaseModel):
    origin: str                       # IATA コード（例: HND）
    destination: str                  # IATA コード or "ANYWHERE"
    departure_date: date
    return_date: Optional[date] = None
    adults: int = 1
    cabin_class: str = "ECONOMY"      # ECONOMY | BUSINESS
    nonstop_only: bool = False
    max_price: Optional[int] = None   # JPY 上限


class FlightItinerary(BaseModel):
    id: str
    departure_iata: str
    arrival_iata: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    stops: int
    airline_code: str
    airline_name: Optional[str] = None
    flight_numbers: List[str] = []
    price_jpy: int
    booking_url: Optional[str] = None
    source_site: str


class FlightSearchResponse(BaseModel):
    origin: str
    destination: str
    departure_date: date
    results: List[FlightItinerary]
    cached: bool = False
    cached_at: Optional[datetime] = None


class PriceCalendarItem(BaseModel):
    date: date
    price_jpy: Optional[int] = None


class PriceCalendarResponse(BaseModel):
    origin: str
    destination: str
    prices: List[PriceCalendarItem]


class InspireDestination(BaseModel):
    destination_iata: str
    destination_name: Optional[str] = None
    country_code: Optional[str] = None
    min_price_jpy: int
    cheapest_date: Optional[date] = None
    duration_days: Optional[int] = None


class InspireResponse(BaseModel):
    origin: str
    destinations: List[InspireDestination]
    cached: bool = False
