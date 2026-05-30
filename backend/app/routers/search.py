"""Full-text-ish search over products GlitchHunter has tracked.

Searches the local `products` table by title (the catalogue the scrapers have
populated), enriches each hit with its latest scraped price and, if present, the
tier of its active deal. Results are ordered by current drop %, biggest first.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..glitch import classify, compute_drop_pct
from ..models import Deal, GlitchTier, PriceHistory, Product
from ..schemas import SearchResultOut

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=list[SearchResultOut])
async def search_products(
    q: str = Query(..., min_length=1, description="Text matched against the product title"),
    store: str | None = Query(None, description="amazon | unieuro | mediaworld"),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    pstmt = select(Product).where(Product.title.ilike(f"%{q}%"))
    if store:
        pstmt = pstmt.where(Product.store == store)
    products = (await db.execute(pstmt.limit(limit))).scalars().all()
    if not products:
        return []

    ids = [p.id for p in products]

    # latest PriceHistory row per matched product
    latest_ts = (
        select(PriceHistory.product_id, func.max(PriceHistory.scraped_at).label("ts"))
        .where(PriceHistory.product_id.in_(ids))
        .group_by(PriceHistory.product_id)
        .subquery()
    )
    price_rows = (
        await db.execute(
            select(PriceHistory).join(
                latest_ts,
                (PriceHistory.product_id == latest_ts.c.product_id)
                & (PriceHistory.scraped_at == latest_ts.c.ts),
            )
        )
    ).scalars().all()
    price_by_pid = {ph.product_id: ph for ph in price_rows}

    # most recent active deal per product (drives tier/drop when present)
    deal_rows = (
        await db.execute(
            select(Deal)
            .where(Deal.product_id.in_(ids), Deal.active.is_(True))
            .order_by(Deal.created_at.desc())
        )
    ).scalars().all()
    deal_by_pid: dict[int, Deal] = {}
    for d in deal_rows:
        deal_by_pid.setdefault(d.product_id, d)  # first seen == most recent

    results: list[SearchResultOut] = []
    for p in products:
        ph = price_by_pid.get(p.id)
        price = ph.price if ph else None
        deal = deal_by_pid.get(p.id)

        if deal:
            reference, drop_pct, tier = deal.old_price, deal.drop_pct, deal.tier
        elif p.reference_price and price is not None:
            reference = p.reference_price
            drop_pct = compute_drop_pct(reference, price)
            tier = classify(reference, price).tier.value
        else:
            reference, drop_pct, tier = p.reference_price, 0.0, GlitchTier.NONE.value

        results.append(
            SearchResultOut(
                product_id=p.id,
                store=p.store,
                title=p.title,
                url=p.url,
                image_url=p.image_url,
                price=price,
                reference_price=reference,
                in_stock=(ph.in_stock if ph else None),
                drop_pct=round(drop_pct, 2),
                tier=tier,
                last_seen=(ph.scraped_at if ph else None),
            )
        )

    results.sort(key=lambda r: r.drop_pct, reverse=True)
    return results
