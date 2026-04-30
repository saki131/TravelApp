"""
空港オートコンプリート ルーター
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from dependencies import verify_api_key
from models import Airport

router = APIRouter(prefix="/api/v1/airports", tags=["airports"])


@router.get("/suggest", dependencies=[Depends(verify_api_key)])
def suggest_airports(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=10, le=30),
    db: Session = Depends(get_db),
):
    """空港名・都市名・IATA コードでオートコンプリート候補を返す。"""
    pattern = f"%{q}%"
    results = db.query(Airport).filter(
        Airport.is_active == True,
        or_(
            Airport.iata_code.ilike(pattern),
            Airport.name_ja.ilike(pattern),
            Airport.name_en.ilike(pattern),
            Airport.city_ja.ilike(pattern),
            Airport.city_en.ilike(pattern),
        )
    ).limit(limit).all()

    return [
        {
            "iata_code": a.iata_code,
            "name_ja": a.name_ja,
            "name_en": a.name_en,
            "city_ja": a.city_ja,
            "city_en": a.city_en,
            "country_code": a.country_code,
        }
        for a in results
    ]
