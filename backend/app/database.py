from collections.abc import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings


def _engine_url_and_args():
    """Normalize the DB URL for asyncpg.

    Free Postgres (Neon, Supabase, …) require SSL and hand out libpq-style URLs
    with `?sslmode=require`, which asyncpg does not understand. Translate that
    (or a plain `?ssl=true`) into asyncpg's own `ssl` connect arg.
    """
    url = make_url(settings.database_url)
    connect_args: dict = {}
    ssl_flag = (url.query.get("sslmode") or url.query.get("ssl") or "").lower()
    if ssl_flag in {"require", "verify-ca", "verify-full", "true", "1", "prefer", "allow"}:
        connect_args["ssl"] = True
        url = url.difference_update_query(["sslmode", "ssl"])
    return url, connect_args


_url, _connect_args = _engine_url_and_args()
engine = create_async_engine(_url, echo=False, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    from . import models  # noqa: F401  (register tables)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
