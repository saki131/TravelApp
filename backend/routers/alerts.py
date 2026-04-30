"""
価格アラート ルーター（F-06）
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import verify_api_key
from models import PriceAlert, Favorite
from schemas.favorite import PriceAlertCreate, PriceAlertOut

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[PriceAlertOut], dependencies=[Depends(verify_api_key)])
def list_alerts(db: Session = Depends(get_db)):
    return db.query(PriceAlert).order_by(PriceAlert.created_at.desc()).all()


@router.post("", response_model=PriceAlertOut, dependencies=[Depends(verify_api_key)])
def create_alert(body: PriceAlertCreate, db: Session = Depends(get_db)):
    # favorite_id の存在確認
    fav = db.query(Favorite).filter(Favorite.id == body.favorite_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")

    alert = PriceAlert(**body.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.put("/{alert_id}", response_model=PriceAlertOut, dependencies=[Depends(verify_api_key)])
def update_alert(alert_id: uuid.UUID, body: PriceAlertCreate, db: Session = Depends(get_db)):
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.target_price_jpy = body.target_price_jpy
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/{alert_id}", dependencies=[Depends(verify_api_key)])
def delete_alert(alert_id: uuid.UUID, db: Session = Depends(get_db)):
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return {"deleted": True}
