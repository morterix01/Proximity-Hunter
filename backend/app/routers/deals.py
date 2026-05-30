from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Deal, Product
from ..schemas import DealOut

router = APIRouter(prefix="/api", tags=["deals"])


@router.get("/deals", response_model=list[DealOut])
async def list_deals(
    store: str | None = Query(None, description="amazon | unieuro | mediaworld"),
    tier: str | None = Query(None, description="error | super"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Deal)
        .options(selectinload(Deal.product))
        .join(Product)
        .where(Deal.active.is_(True))
        .order_by(Deal.created_at.desc())
        .limit(limit)
    )
    if store:
        stmt = stmt.where(Product.store == store)
    if tier:
        stmt = stmt.where(Deal.tier == tier)

    deals = (await db.execute(stmt)).scalars().all()

    return [
        DealOut(
            id=d.id,
            store=d.product.store,
            title=d.product.title,
            url=d.product.url,
            image_url=d.product.image_url,
            tier=d.tier,
            old_price=d.old_price,
            new_price=d.new_price,
            drop_pct=d.drop_pct,
            created_at=d.created_at,
        )
        for d in deals
    ]
