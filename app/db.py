from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.engine import make_url

from .config import settings


class Base(DeclarativeBase):
    pass


# Normalize the DATABASE URL to use asyncpg when using async engine.
# This avoids requiring psycopg2 (which needs pg_config to build on some Python versions).
db_url = settings.database_url
if db_url:
    # handle Heroku-style DATABASE_URL (postgres://) and plain postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    db_url,
    future=True,
)


SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db():
    from .models import (
        Job,
        Application,
        ProfileFact,
        AuditEvent,
        Message,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with SessionLocal() as session:
        yield session
