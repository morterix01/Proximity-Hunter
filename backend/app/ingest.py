import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .glitch import classify
from .models import Deal, GlitchTier, PriceHistory, Product
from .schemas import ScrapedItem

log = logging.getLogger(__name__)


async def _get_or_create_product(db: AsyncSession, item: ScrapedItem) -> Product:
    res = await db.execute(
        select(Product).where(
            Product.store == item.store, Product.external_id == item.external_id
        )
    )
    product = res.scalar_one_or_none()
    if product is None:
        product = Product(
            store=item.store,
            external_id=item.external_id,
            title=item.title,
            url=item.url,
            image_url=item.image_url,
            reference_price=item.reference_price,
        )
        db.add(product)
        await db.flush()
    else:
        product.title = item.title
        product.image_url = item.image_url or product.image_url
        if item.reference_price:
            product.reference_price = item.reference_price
    return product


async def _reference_price(db: AsyncSession, product: Product, item: ScrapedItem) -> float | None:
    """Baseline to measure the drop against.

    Priority: explicit struck price on the page > stored reference > the max of the
    recent price history (the 'normal' level before the dip).
    """
    candidates: list[float] = []
    if item.reference_price:
        candidates.append(item.reference_price)
    if product.reference_price:
        candidates.append(product.reference_price)

    res = await db.execute(
        select(PriceHistory.price)
        .where(PriceHistory.product_id == product.id)
        .order_by(PriceHistory.scraped_at.desc())
        .limit(20)
    )
    candidates.extend([p for (p,) in res.all()])

    candidates = [c for c in candidates if c and c > 0]
    return max(candidates) if candidates else None


async def ingest_item(db: AsyncSession, item: ScrapedItem) -> Deal | None:
    """Persist one scraped item and return a freshly created Deal, if any."""
    product = await _get_or_create_product(db, item)

    reference = await _reference_price(db, product, item)

    db.add(PriceHistory(product_id=product.id, price=item.price, in_stock=item.in_stock))

    if reference is None:
        return None  # first sighting, nothing to compare yet

    result = classify(reference, item.price)
    if result.tier == GlitchTier.NONE:
        return None

    # Deduplicate: skip if an active deal at this price already exists.
    existing = await db.execute(
        select(Deal).where(
            Deal.product_id == product.id,
            Deal.active.is_(True),
            Deal.new_price == item.price,
        )
    )
    if existing.scalar_one_or_none():
        return None

    deal = Deal(
        product_id=product.id,
        tier=result.tier.value,
        old_price=result.old_price,
        new_price=result.new_price,
        drop_pct=result.drop_pct,
        active=True,
        notified=False,
    )
    db.add(deal)
    await db.flush()
    log.info(
        "GLITCH %s %s -%.0f%% (%.2f -> %.2f)",
        product.store, result.tier.value, result.drop_pct,
        result.old_price, result.new_price,
    )
    return deal


async def ingest_batch(db: AsyncSession, items: list[ScrapedItem]) -> list[Deal]:
    deals: list[Deal] = []
    for item in items:
        try:
            deal = await ingest_item(db, item)
            if deal:
                deals.append(deal)
        except Exception:
            log.exception("ingest failed for %s/%s", item.store, item.external_id)
    await db.commit()
    return deals
