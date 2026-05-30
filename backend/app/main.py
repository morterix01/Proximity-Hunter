import logging
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .notifications import init_firebase
from .routers import deals, devices, search
from .tasks import scrape_all

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    init_firebase()
    try:
        app.state.redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    except Exception as exc:
        log.warning("Redis pool unavailable, /admin/scrape will run inline: %s", exc)
        app.state.redis = None
    yield
    if app.state.redis is not None:
        await app.state.redis.close()


app = FastAPI(title="GlitchHunter API", version="1.0.0", lifespan=lifespan)

# Allow the SwiftUI app and the static HTML preview (origin "null" from file://)
# to call the API from the browser. Tighten allow_origins for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deals.router)
app.include_router(devices.router)
app.include_router(search.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/admin/scrape", tags=["admin"])
async def trigger_scrape():
    """Kick a scrape cycle. Enqueues to the arq worker if Redis is up,
    otherwise runs inline (handy for local dev without a worker)."""
    if app.state.redis is not None:
        job = await app.state.redis.enqueue_job("scrape_job")
        return {"queued": True, "job_id": job.job_id if job else None}
    summary = await scrape_all()
    return {"queued": False, "ran_inline": True, **summary}
