from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    PERSONAL_API_KEY: str = "changeme"

    # SerpApi (Google Flights)
    SERPAPI_KEY: str = ""

    # Amadeus API (廃止予定 2026-07-17 - レガシー互換のため残置)
    AMADEUS_CLIENT_ID: str = ""
    AMADEUS_CLIENT_SECRET: str = ""
    AMADEUS_BASE_URL: str = "https://test.api.amadeus.com"

    # Kiwi API（フォールバック）
    KIWI_API_KEY: str = ""

    # Trip.com Affiliate（Phase 2）
    TRIPCOM_AFFILIATE_ID: str = ""
    TRIPCOM_API_KEY: str = ""

    # Gemini AI（レート制限対策: 最大3キーをローテーション）
    GEMINI_API_KEY: str = ""
    GEMINI_API_KEY_2: str = ""
    GEMINI_API_KEY_3: str = ""

    # Web Push (VAPID)
    WEBPUSH_VAPID_PRIVATE_KEY: str = ""
    WEBPUSH_VAPID_PUBLIC_KEY: str = ""
    WEBPUSH_VAPID_CLAIMS_SUB: str = "mailto:admin@example.com"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
