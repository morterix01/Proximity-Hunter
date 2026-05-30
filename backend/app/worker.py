"""arq worker: scheduled scrape cycles + on-demand jobs enqueued by the API.

Run with:  arq app.worker.WorkerSettings
"""
import logging

from arq import cron
from arq.connections import RedisSettings

from .config import settings
from .database import init_db
from .tasks import scrape_all

logging.basicConfig(level=logging.INFO)


async def scrape_job(ctx: dict) -> dict:
    return await scrape_all()


async def startup(ctx: dict) -> None:
    await init_db()


# Cadence: SCRAPE_INTERVAL_SECONDS rounded to a minute granularity. Default 900s
# (15 min) -> run at minutes {0,15,30,45}. Adjust the set for other intervals.
_step = max(1, settings.scrape_interval_seconds // 60)
_minutes = set(range(0, 60, min(_step, 59)))


class WorkerSettings:
    functions = [scrape_job]
    on_startup = startup
    cron_jobs = [cron(scrape_job, minute=_minutes, run_at_startup=True)]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
