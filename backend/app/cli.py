"""Run one scrape cycle from the command line / CI cron.

    python -m app.cli

Used by the GitHub Actions schedule so the scraper runs "h24" for free without
an always-on worker. Reuses the same pipeline as the arq worker (tasks.scrape_all):
init the DB, init Firebase (no-op without creds), scrape → ingest → push.
"""
import asyncio
import logging

from .database import init_db
from .notifications import init_firebase
from .tasks import scrape_all

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("glitchhunter.cli")


async def _run() -> None:
    await init_db()
    init_firebase()
    summary = await scrape_all()
    log.info("scrape cycle finished: %s", summary)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
