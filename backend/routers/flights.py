"""
フライト検索 ルーター
F-02: 同区間フライト検索
F-02b: どこでも検索
F-03: 価格カレンダー
"""
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import verify_api_key
from schemas.flight import (
    FlightSearchRequest, FlightSearchResponse, FlightItinerary,
    PriceCalendarResponse, PriceCalendarItem,
    InspireResponse, InspireDestination,
)
from services.serpapi import serpapi_client
from services.cache import (
    get_flight_cache, set_flight_cache,
    get_calendar_cache, set_calendar_cache,
    get_inspire_cache, set_inspire_cache,
)

router = APIRouter(prefix="/api/v1/flights", tags=["flights"])
logger = logging.getLogger(__name__)


def _parse_flights(raw: dict) -> list[FlightItinerary]:
    """SerpApi Google Flights レスポンスを FlightItinerary リストに変換する。"""
    results = []

    all_flights = raw.get("best_flights", []) + raw.get("other_flights", [])
    for idx, offer in enumerate(all_flights):
        try:
            price = offer.get("price")
            if price is None:
                continue
            price_jpy = int(price)

            legs = offer.get("flights", [])
            if not legs:
                continue

            first_leg = legs[0]
            last_leg  = legs[-1]

            dep_airport = first_leg.get("departure_airport", {})
            arr_airport = last_leg.get("arrival_airport", {})

            dep_str = dep_airport.get("time", "")
            arr_str = arr_airport.get("time", "")

            dep_time = datetime.fromisoformat(dep_str) if dep_str else datetime.now(timezone.utc)
            arr_time = datetime.fromisoformat(arr_str) if arr_str else dep_time

            stops = max(0, len(legs) - 1)

            airline_code = first_leg.get("airline", "")
            airline_name = first_leg.get("airline_logo", airline_code)  # ロゴURLか airline_code
            # airline 正式名を取得
            airline_name = first_leg.get("airline", airline_code)

            flight_nums = [leg.get("flight_number", "") for leg in legs if leg.get("flight_number")]

            duration_min = offer.get("total_duration") or 0

            dep_iata = dep_airport.get("id", "")
            arr_iata = arr_airport.get("id", "")

            results.append(FlightItinerary(
                id=f"serpapi_{idx}",
                departure_iata=dep_iata,
                arrival_iata=arr_iata,
                departure_time=dep_time,
                arrival_time=arr_time,
                duration_minutes=duration_min,
                stops=stops,
                airline_code=airline_code,
                airline_name=airline_name,
                flight_numbers=flight_nums,
                price_jpy=price_jpy,
                source_site="google_flights",
            ))
        except Exception as e:
            logger.debug("Flight parse error: %s", e)
            continue
    return results


# ------------------------------------------------------------------
# F-02: フライト検索
# ------------------------------------------------------------------
@router.post("/search", response_model=FlightSearchResponse, dependencies=[Depends(verify_api_key)])
async def search_flights(req: FlightSearchRequest, db: Session = Depends(get_db)):
    query_hash = serpapi_client.make_query_hash(
        origin=req.origin,
        destination=req.destination,
        departure_date=req.departure_date.isoformat(),
        return_date=req.return_date.isoformat() if req.return_date else None,
        adults=req.adults,
        cabin_class=req.cabin_class,
        nonstop_only=req.nonstop_only,
    )

    cached = get_flight_cache(db, query_hash)
    if cached:
        itineraries = [FlightItinerary(**i) for i in cached.get("results", [])]
        return FlightSearchResponse(
            origin=req.origin,
            destination=req.destination,
            departure_date=req.departure_date,
            results=itineraries,
            cached=True,
        )

    try:
        raw = await serpapi_client.search_flights(
            origin=req.origin,
            destination=req.destination,
            departure_date=req.departure_date,
            return_date=req.return_date,
            adults=req.adults,
            travel_class=req.cabin_class,
            nonstop=req.nonstop_only,
        )
    except Exception as e:
        logger.error("SerpApi search error: %s", e)
        raise HTTPException(status_code=502, detail="フライト検索 API でエラーが発生しました")

    itineraries = _parse_flights(raw)
    if req.max_price:
        itineraries = [i for i in itineraries if i.price_jpy <= req.max_price]

    # キャッシュ保存
    try:
        set_flight_cache(
            db, query_hash,
            {"results": [i.model_dump() for i in itineraries]},
            origin_iata=req.origin,
            destination_iata=req.destination,
            departure_date=req.departure_date,
            return_date=req.return_date,
            source_api="google_flights",
            result_count=len(itineraries),
        )
    except Exception as e:
        logger.warning("Cache save failed: %s", e)

    return FlightSearchResponse(
        origin=req.origin,
        destination=req.destination,
        departure_date=req.departure_date,
        results=itineraries,
        cached=False,
    )


# ------------------------------------------------------------------
# F-03: 価格カレンダー
# ------------------------------------------------------------------
@router.get("/price-calendar", response_model=PriceCalendarResponse, dependencies=[Depends(verify_api_key)])
async def price_calendar(
    origin: str = Query(..., min_length=3, max_length=3),
    destination: str = Query(..., min_length=3, max_length=3),
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    """指定路線の月別価格カレンダーを返す。"""
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    date_from = date(year, month, 1)
    date_to   = date(year, month, last_day)

    # キャッシュから取得
    prices = []
    missing_dates = []
    current = date_from
    while current <= date_to:
        cached_price = get_calendar_cache(db, origin, destination, current)
        if cached_price is not None:
            prices.append(PriceCalendarItem(date=current, price_jpy=cached_price))
        else:
            missing_dates.append(current)
        current += timedelta(days=1)

    # キャッシュ未ヒット分を SerpApi で取得
    if missing_dates:
        try:
            range_str = f"{date_from.isoformat()},{date_to.isoformat()}"
            raw = await serpapi_client.get_flight_dates(
                origin=origin,
                destination=destination,
                departure_date=range_str,
            )
            new_prices = []
            for item in raw.get("data", []):
                d = date.fromisoformat(item.get("departureDate", ""))
                price_raw = item.get("price", {}).get("total", "0")
                pjpy = int(float(price_raw))
                new_prices.append({"date": d, "price_jpy": pjpy})
                prices.append(PriceCalendarItem(date=d, price_jpy=pjpy))

            set_calendar_cache(db, origin, destination, new_prices)
        except Exception as e:
            logger.error("price-calendar SerpApi error: %s", e)
            # エラー時は不明として返す
            for d in missing_dates:
                prices.append(PriceCalendarItem(date=d, price_jpy=None))

    prices.sort(key=lambda x: x.date)
    return PriceCalendarResponse(origin=origin, destination=destination, prices=prices)


# ------------------------------------------------------------------
# F-02b: どこでも検索
# ------------------------------------------------------------------
@router.get("/inspire", response_model=InspireResponse, dependencies=[Depends(verify_api_key)])
async def inspire(
    origin: str = Query(..., min_length=3, max_length=3),
    date_from: date = Query(...),
    date_to: date = Query(...),
    max_price: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    """日時と出発地を固定して複数行先の最安値を返す（どこでも検索）。"""
    query_hash = serpapi_client.make_query_hash(
        origin=origin,
        date_from=date_from.isoformat(),
        date_to=date_to.isoformat(),
        max_price=max_price,
    )

    cached = get_inspire_cache(db, query_hash)
    if cached:
        destinations = [InspireDestination(**d) for d in cached.get("destinations", [])]
        return InspireResponse(origin=origin, destinations=destinations, cached=True)

    try:
        raw = await serpapi_client.get_flight_inspirations(
            origin=origin,
            departure_date=f"{date_from.isoformat()},{date_to.isoformat()}",
            max_price=max_price,
        )
    except Exception as e:
        logger.error("inspire SerpApi error: %s", e)
        raise HTTPException(status_code=502, detail="インスピレーション API でエラーが発生しました")

    destinations = []
    for item in raw.get("data", []):
        try:
            price_raw = item.get("price", {}).get("total", "0")
            destinations.append(InspireDestination(
                destination_iata=item.get("destination", ""),
                min_price_jpy=int(float(price_raw)),
                cheapest_date=date.fromisoformat(item.get("departureDate", date.today().isoformat())),
            ))
        except Exception:
            continue

    if max_price:
        destinations = [d for d in destinations if d.min_price_jpy <= max_price]

    destinations.sort(key=lambda x: x.min_price_jpy)

    try:
        set_inspire_cache(
            db, query_hash,
            {"destinations": [d.model_dump() for d in destinations]},
            origin_iata=origin,
            departure_date_from=date_from,
            departure_date_to=date_to,
            max_price_jpy=max_price,
        )
    except Exception as e:
        logger.warning("inspire cache save failed: %s", e)

    return InspireResponse(origin=origin, destinations=destinations, cached=False)
