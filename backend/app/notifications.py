import logging
import os

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .models import Deal, Device, Product

log = logging.getLogger(__name__)
_initialized = False


def init_firebase() -> bool:
    """Init firebase-admin once. No-op (logs) if creds file missing."""
    global _initialized
    if _initialized:
        return True
    path = settings.firebase_credentials
    if not path or not os.path.exists(path):
        log.warning("Firebase creds not found at %s; push disabled.", path)
        return False
    firebase_admin.initialize_app(credentials.Certificate(path))
    _initialized = True
    log.info("Firebase initialized.")
    return True


def _build_message(token: str, product: Product, deal: Deal) -> messaging.Message:
    is_error = deal.tier == "error"
    title = "🚨 Errore Prezzo!" if is_error else "🔥 Super Sconto"
    body = f"{product.title[:60]} • -{deal.drop_pct:.0f}% → €{deal.new_price:.2f}"
    return messaging.Message(
        token=token,
        notification=messaging.Notification(title=title, body=body),
        data={
            "deal_id": str(deal.id),
            "store": product.store,
            "tier": deal.tier,
            "url": product.url,
            "new_price": f"{deal.new_price:.2f}",
            "old_price": f"{deal.old_price:.2f}",
            "drop_pct": f"{deal.drop_pct:.2f}",
        },
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound="default", badge=1, content_available=True)
            )
        ),
    )


async def notify_error_deal(db: AsyncSession, deal: Deal) -> int:
    """Push a single deal to every registered device. Returns success count.

    Per the spec only 'Errore Prezzo' triggers a push; tweak here to also push
    'super' deals.
    """
    if deal.tier != "error":
        return 0
    if not init_firebase():
        return 0

    product = await db.get(Product, deal.product_id)
    if product is None:
        return 0

    tokens = [t for (t,) in (await db.execute(select(Device.fcm_token))).all()]
    if not tokens:
        return 0

    sent = 0
    stale: list[str] = []
    for token in tokens:
        try:
            messaging.send(_build_message(token, product, deal))
            sent += 1
        except messaging.UnregisteredError:
            stale.append(token)
        except Exception as exc:
            log.warning("push failed for token %s…: %s", token[:12], exc)

    # Prune tokens FCM reports as unregistered.
    for token in stale:
        dev = (
            await db.execute(select(Device).where(Device.fcm_token == token))
        ).scalar_one_or_none()
        if dev:
            await db.delete(dev)

    deal.notified = True
    await db.commit()
    log.info("pushed deal %s to %d/%d devices", deal.id, sent, len(tokens))
    return sent
