from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# Enable SSL for external databases (e.g. Supabase)
_connect_args = {}
if "supabase" in settings.DATABASE_URL or "pooler.supabase" in settings.DATABASE_URL:
    import ssl as _ssl
    _ctx = _ssl.create_default_context()
    _ctx.check_hostname = False
    _ctx.verify_mode = _ssl.CERT_NONE
    _connect_args = {"ssl": _ctx}

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=20, max_overflow=10, connect_args=_connect_args)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine + session factory for Celery workers (uses psycopg2 driver)
_sync_engine = None
_sync_session = None


def sync_session_factory() -> Session:
    """Return a sync Session for use in Celery tasks. Lazily initializes the sync engine."""
    global _sync_engine, _sync_session
    if _sync_engine is None:
        sync_url = settings.DATABASE_URL_SYNC
        if not sync_url:
            # Derive sync URL from async URL by swapping driver
            sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        _sync_engine = create_engine(sync_url, echo=False, pool_size=5, max_overflow=5)
        _sync_session = sessionmaker(bind=_sync_engine, expire_on_commit=False)
    return _sync_session()


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
