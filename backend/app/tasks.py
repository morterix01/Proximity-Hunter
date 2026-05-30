import logging

from .database import SessionLocal
from .ingest import ingest_batch
from .notifications import notify_error_deal
from .scrapers import SCRAPERS

log = logging.getLogger(__name__)


async def scrape_all() -> dict:
    """One full cycle: run every scraper, persist prices, raise + push glitches.

    Returns a small summary dict for logging / API responses.
    """
    scraped = 0
    new_deals = 0
    pushed = 0

    async with SessionLocal() as db:
        for scraper in SCRAPERS:
            try:
                items = await scraper.scrape()
            except Exception:
                log.exception("scraper %s crashed", scraper.store)
                continue

            scraped += len(items)
            deals = await ingest_batch(db, items)
            new_deals += len(deals)

            for deal in deals:
                pushed += await notify_error_deal(db, deal)

    summary = {"scraped": scraped, "new_deals": new_deals, "pushed": pushed}
    log.info("scrape cycle done: %s", summary)
    return summary
