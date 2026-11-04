from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine_kwargs = {
    "echo": False,
    "future": True,
    "pool_pre_ping": True,
}

if settings.SQLALCHEMY_DATABASE_URI and settings.SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 10

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    **engine_kwargs
)


# Async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
