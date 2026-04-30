"""
SerpApi (Google Flights) クライアント
Amadeus Client の代替実装。同じメソッドシグネチャを維持する。
"""
import hashlib
import json
import logging
from datetime import date, datetime
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

SERPAPI_BASE_URL = "https://serpapi.com/search"


class SerpApiClient:
    """SerpApi Google Flights ラッパー。"""

    def __init__(self):
        self.api_key = settings.SERPAPI_KEY

    # ------------------------------------------------------------------
    # フライト検索
    # ------------------------------------------------------------------
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: Optional[date] = None,
        adults: int = 1,
        travel_class: str = "ECONOMY",
        nonstop: bool = False,
        max: int = 10,
    ) -> dict:
        """
        Google Flights でフライトを検索し、SerpApi レスポンスをそのまま返す。
        travel_class 対応: ECONOMY→1, PREMIUM_ECONOMY→2, BUSINESS→3, FIRST→4
        """
        class_map = {
            "ECONOMY": 1,
            "PREMIUM_ECONOMY": 2,
            "BUSINESS": 3,
            "FIRST": 4,
        }
        travel_class_num = class_map.get(travel_class.upper(), 1)

        # 往復 or 片道
        trip_type = 1 if return_date else 2  # 1=round trip, 2=one way

        params: dict = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": departure_date.isoformat() if hasattr(departure_date, "isoformat") else str(departure_date),
            "currency": "JPY",
            "hl": "ja",
            "adults": adults,
            "travel_class": travel_class_num,
            "type": trip_type,
            "api_key": self.api_key,
        }
        if return_date:
            params["return_date"] = return_date.isoformat() if hasattr(return_date, "isoformat") else str(return_date)
        if nonstop:
            params["stops"] = 0  # 0 = nonstop only

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(SERPAPI_BASE_URL, params=params)
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # 価格カレンダー
    # ------------------------------------------------------------------
    async def get_flight_dates(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[str] = None,
        one_way: bool = True,
    ) -> dict:
        """
        Google Flights で価格カレンダーデータを取得する。
        departure_date が "YYYY-MM-DD,YYYY-MM-DD" 形式の場合は最初の日付を使用。
        レスポンスは Amadeus 互換の {"data": [...]} 形式に正規化して返す。
        """
        # departure_date が "from,to" 形式の場合は from を使用
        outbound_date = None
        if departure_date:
            if "," in departure_date:
                outbound_date = departure_date.split(",")[0].strip()
            else:
                outbound_date = departure_date

        trip_type = 2 if one_way else 1

        params: dict = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "currency": "JPY",
            "hl": "ja",
            "type": trip_type,
            "show_hidden": "true",
            "api_key": self.api_key,
        }
        if outbound_date:
            params["outbound_date"] = outbound_date

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(SERPAPI_BASE_URL, params=params)
            resp.raise_for_status()
            raw = resp.json()

        # Amadeus 互換の形式に正規化
        return self._normalize_price_calendar(raw)

    def _normalize_price_calendar(self, raw: dict) -> dict:
        """
        SerpApi の price_insights / best_flights レスポンスを
        Amadeus Flight Dates 互換の {"data": [{"departureDate": "...", "price": {"total": "..."}}]}
        形式に変換する。
        """
        data = []

        # price_insights に月別データがある場合
        price_insights = raw.get("price_insights", {})
        price_history = price_insights.get("price_history", [])
        for item in price_history:
            # item は [date_str, price_int] 形式
            if isinstance(item, list) and len(item) >= 2:
                entry_date = item[0]
                entry_price = item[1]
                data.append({
                    "departureDate": entry_date,
                    "price": {"total": str(entry_price), "currency": "JPY"},
                })

        # best_flights からも価格を収集（フォールバック）
        if not data:
            for flight in raw.get("best_flights", []) + raw.get("other_flights", []):
                dep_date = None
                for leg in flight.get("flights", []):
                    dep_dt = leg.get("departure_airport", {}).get("time", "")
                    if dep_dt:
                        dep_date = dep_dt[:10]
                        break
                price = flight.get("price")
                if dep_date and price is not None:
                    data.append({
                        "departureDate": dep_date,
                        "price": {"total": str(price), "currency": "JPY"},
                    })

        return {"data": data, "_raw": raw}

    # ------------------------------------------------------------------
    # どこでも検索（Travel Explore）
    # ------------------------------------------------------------------
    async def get_flight_inspirations(
        self,
        origin: str,
        departure_date: Optional[str] = None,
        max_price: Optional[int] = None,
        one_way: bool = True,
    ) -> dict:
        """
        Google Travel Explore でインスピレーション（複数行先の最安値）を取得する。
        レスポンスを Amadeus 互換の {"data": [...]} 形式に正規化して返す。
        """
        params: dict = {
            "engine": "google_travel_explore",
            "q": "Flights",
            "departure_id": origin,
            "currency": "JPY",
            "hl": "ja",
            "api_key": self.api_key,
        }

        # google_travel_explore は outbound_date 非対応のため日付パラメータは送らない

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(SERPAPI_BASE_URL, params=params)
            resp.raise_for_status()
            raw = resp.json()

        return self._normalize_inspirations(raw)

    def _normalize_inspirations(self, raw: dict) -> dict:
        """
        SerpApi Google Travel Explore レスポンスを
        Amadeus Flight Destinations 互換の形式に変換する。
        実際のレスポンス構造:
          destination_airport.code  → IATAコード
          flight_price              → 価格(JPY整数)
          start_date                → 出発日
        """
        data = []
        for item in raw.get("destinations", []):
            try:
                airport = item.get("destination_airport") or {}
                destination = airport.get("code", "")
                price = item.get("flight_price")
                dep_date = item.get("start_date") or date.today().isoformat()
                if destination and price is not None:
                    data.append({
                        "destination": destination,
                        "departureDate": dep_date,
                        "price": {"total": str(price), "currency": "JPY"},
                    })
            except Exception as e:
                logger.debug("inspire parse error: %s", e)
                continue

        return {"data": data, "_raw": raw}

    # ------------------------------------------------------------------
    # ユーティリティ: 検索クエリのハッシュ生成
    # ------------------------------------------------------------------
    @staticmethod
    def make_query_hash(**kwargs) -> str:
        normalized = json.dumps(dict(sorted(kwargs.items())), sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()


# シングルトン
serpapi_client = SerpApiClient()
