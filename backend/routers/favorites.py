"""
お気に入り・Web Push 購読 ルーター（F-06）
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import verify_api_key
from models import Favorite, PushSubscription
from schemas.favorite import (
    FavoriteCreate, FavoriteOut,
    PushSubscriptionCreate, PushSubscriptionOut,
)

router = APIRouter(prefix="/api/v1/favorites", tags=["favorites"])


# ------------------------------------------------------------------
# お気に入り
# ------------------------------------------------------------------
@router.get("", response_model=list[FavoriteOut], dependencies=[Depends(verify_api_key)])
def list_favorites(db: Session = Depends(get_db)):
    return db.query(Favorite).order_by(Favorite.created_at.desc()).all()


@router.post("", response_model=FavoriteOut, dependencies=[Depends(verify_api_key)])
def create_favorite(body: FavoriteCreate, db: Session = Depends(get_db)):
    fav = Favorite(**body.model_dump())
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


@router.delete("/{fav_id}", dependencies=[Depends(verify_api_key)])
def delete_favorite(fav_id: uuid.UUID, db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter(Favorite.id == fav_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()
    return {"deleted": True}


# ------------------------------------------------------------------
# Web Push 購読登録
# ------------------------------------------------------------------
@router.post("/push-subscribe", response_model=PushSubscriptionOut, dependencies=[Depends(verify_api_key)])
def subscribe_push(body: PushSubscriptionCreate, db: Session = Depends(get_db)):
    existing = db.query(PushSubscription).filter(
        PushSubscription.endpoint == body.endpoint
    ).first()
    if existing:
        return existing

    sub = PushSubscription(**body.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub
