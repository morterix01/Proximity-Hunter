from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Device, utcnow
from ..schemas import DeviceOut, DeviceRegisterIn

router = APIRouter(prefix="/api/device", tags=["devices"])


@router.post("/register", response_model=DeviceOut)
async def register_device(payload: DeviceRegisterIn, db: AsyncSession = Depends(get_db)):
    """Idempotent: upsert by FCM token, refresh last_seen."""
    existing = (
        await db.execute(select(Device).where(Device.fcm_token == payload.fcm_token))
    ).scalar_one_or_none()

    if existing:
        existing.last_seen = utcnow()
        existing.platform = payload.platform
        await db.commit()
        return existing

    device = Device(fcm_token=payload.fcm_token, platform=payload.platform)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device
