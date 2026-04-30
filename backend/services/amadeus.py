"""
Amadeus API クライアント
ドキュメント: https://developers.amadeus.com/self-service
"""
import hashlib
import json
from datetime import date, datetime, timedelta
from typing import Optional

import httpx

from config import settings


class AmadeusClient:
    """Amadeus REST API のシンプルなラッパー。トークンを自動更新する。"""

    def __init__(self):
        self.base_url = settings.AMADEUS_BASE_URL.rstrip("/")
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    # ------------------------------------------------------------------
    # 認証
    # ------------------------------------------------------------------
    async def _get_token(self) -> str:
        """OAuth2 client_credentials トークンを取得（期限切れ時は再取得）。"""
        if self._token and self._token_expires_at and datetime.utcnow() < self._token_expires_at:
            return self._token

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{self.base_url}/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.AMADEUS_CLIENT_ID,
                    "client_secret": settings.AMADEUS_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            expires_in = int(data.get("expires_in", 1799))
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
            return self._token

    # ------------------------------------------------------------------
    # フライト検索（Flight Offers Search）
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
        max: int = 30,
    ) -> dict:
        token = await self._get_token()
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date.isoformat(),
            "adults": adults,
            "travelClass": travel_class,
            "max": max,
            "currencyCode": "JPY",
        }
        if return_date:
            params["returnDate"] = return_date.isoformat()
        if nonstop:
            params["nonStop"] = "true"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.base_url}/v2/shopping/flight-offers",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # 価格カレンダー（Flight Dates）
    # ------------------------------------------------------------------
    async def get_flight_dates(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[str] = None,
        one_way: bool = True,
    ) -> dict:
        token = await self._get_token()
        params = {
            "origin": origin,
            "destination": destination,
            "oneWay": str(one_way).lower(),
            "nonStop": "false",
            "viewBy": "DATE",
        }
        if departure_date:
            params["departureDate"] = departure_date

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.base_url}/v1/shopping/flight-dates",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # どこでも検索（Flight Inspirations）
    # ------------------------------------------------------------------
    async def get_flight_inspirations(
        self,
        origin: str,
        departure_date: Optional[str] = None,
        max_price: Optional[int] = None,
        one_way: bool = True,
    ) -> dict:
        token = await self._get_token()
        params = {
            "origin": origin,
            "oneWay": str(one_way).lower(),
            "nonStop": "false",
            "viewBy": "DESTINATION",
        }
        if departure_date:
            params["departureDate"] = departure_date
        if max_price:
            params["maxPrice"] = max_price

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.base_url}/v1/shopping/flight-destinations",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # ユーティリティ: 検索クエリのハッシュ生成
    # ------------------------------------------------------------------
    @staticmethod
    def make_query_hash(**kwargs) -> str:
        normalized = json.dumps(dict(sorted(kwargs.items())), sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()


# シングルトン
amadeus_client = AmadeusClient()
