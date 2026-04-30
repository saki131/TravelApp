"""
Web Push 通知サービス（pywebpush）
"""
import json
import logging
from typing import Optional

from pywebpush import webpush, WebPushException
from sqlalchemy.orm import Session
from models import PushSubscription, PriceAlert, Favorite
from config import settings

logger = logging.getLogger(__name__)


def send_push(subscription: PushSubscription, title: str, body: str, url: str = "/") -> bool:
    """単一デバイスに Web Push を送信する。"""
    if not settings.WEBPUSH_VAPID_PRIVATE_KEY:
        logger.warning("VAPID キーが未設定のため Web Push はスキップします")
        return False
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps({"title": title, "body": body, "url": url}),
            vapid_private_key=settings.WEBPUSH_VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": settings.WEBPUSH_VAPID_CLAIMS_SUB,
            },
        )
        return True
    except WebPushException as e:
        logger.error("Web Push 送信失敗 [%s]: %s", subscription.endpoint[:40], e)
        return False


def notify_all(db: Session, title: str, body: str, url: str = "/") -> int:
    """全購読デバイスに送信し、送信成功数を返す。"""
    subs = db.query(PushSubscription).all()
    ok = sum(1 for s in subs if send_push(s, title, body, url))
    return ok
