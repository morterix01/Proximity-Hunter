"""User-editable watchlist: which product URLs GlitchHunter should monitor.

The scrapers read their targets from this table (see tasks.scrape_all), so a user
can add/remove products from the app instead of editing hard-coded URL lists.
"""
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Watch
from ..schemas import WatchIn, WatchOut

router = APIRouter(prefix="/api/watch", tags=["watch"])

SUPPORTED = {"amazon", "unieuro", "mediaworld"}
_DOMAIN_HINTS = {"amazon": "amazon", "unieuro": "unieuro", "mediaworld": "mediaworld"}


def detect_store(url: str) -> str | None:
    host = (urlparse(url).hostname or "").lower()
    for frag, store in _DOMAIN_HINTS.items():
        if frag in host:
            return store
    return None


@router.get("", response_model=list[WatchOut])
async def list_watch(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Watch).order_by(Watch.created_at.desc()))).scalars().all()
    return rows


@router.post("", response_model=WatchOut)
async def add_watch(payload: WatchIn, db: AsyncSession = Depends(get_db)):
    store = (payload.store or detect_store(payload.url) or "").lower()
    if store not in SUPPORTED:
        raise HTTPException(
            status_code=400,
            detail="Unknown store. Use an amazon/unieuro/mediaworld URL or pass `store`.",
        )
    existing = (
        await db.execute(select(Watch).where(Watch.url == payload.url))
    ).scalar_one_or_none()
    if existing:
        return existing

    watch = Watch(store=store, url=payload.url, title=payload.title)
    db.add(watch)
    await db.commit()
    await db.refresh(watch)
    return watch


@router.delete("/{watch_id}")
async def remove_watch(watch_id: int, db: AsyncSession = Depends(get_db)):
    watch = await db.get(Watch, watch_id)
    if watch:
        await db.delete(watch)
        await db.commit()
    return {"deleted": bool(watch)}
