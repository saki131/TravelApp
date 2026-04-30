"""
セール情報 ルーター
F-01: セール・クーポンカレンダー
"""
from typing import Optional
from datetime import date
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import get_db
from dependencies import verify_api_key
from models import SaleEvent
from schemas.sale import SaleEventOut, SaleListResponse

router = APIRouter(prefix="/api/v1/sales", tags=["sales"])


@router.get("", response_model=SaleListResponse, dependencies=[Depends(verify_api_key)])
def list_sales(
    category: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date]   = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    """セール一覧（カレンダー表示用）。"""
    q = db.query(SaleEvent)

    if category:
        q = q.filter(SaleEvent.category == category)

    if date_from:
        q = q.filter(
            or_(SaleEvent.sale_end >= date_from, SaleEvent.sale_end.is_(None))
        )

    if date_to:
        q = q.filter(
            or_(SaleEvent.sale_start <= date_to, SaleEvent.sale_start.is_(None))
        )

    total = q.count()
    items = q.order_by(SaleEvent.created_at.desc()).offset(offset).limit(limit).all()

    return SaleListResponse(total=total, items=items)


@router.get("/today", response_model=SaleListResponse, dependencies=[Depends(verify_api_key)])
def today_sales(db: Session = Depends(get_db)):
    """本日有効なセール（ダッシュボード表示用）。"""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    q = db.query(SaleEvent).filter(
        or_(SaleEvent.sale_start <= now, SaleEvent.sale_start.is_(None)),
        or_(SaleEvent.sale_end >= now, SaleEvent.sale_end.is_(None)),
    ).order_by(SaleEvent.created_at.desc()).limit(20)
    items = q.all()
    return SaleListResponse(total=len(items), items=items)


@router.get("/{sale_id}", response_model=SaleEventOut, dependencies=[Depends(verify_api_key)])
def get_sale(sale_id: uuid.UUID, db: Session = Depends(get_db)):
    """セール詳細。"""
    from fastapi import HTTPException
    event = db.query(SaleEvent).filter(SaleEvent.id == sale_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Sale not found")
    return event
