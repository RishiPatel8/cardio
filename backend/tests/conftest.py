import pytest
import os
import uuid
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app as fastapi_app
from app.core.dependencies import get_current_user, get_db, get_redis
import app.core.dependencies
from app.models.user import User
from app.database.base import Base

# DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test.db"))
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://cardioguard_admin:production_secure_db_pass_1298@localhost:5432/cardioguard_db_test"

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

from sqlalchemy import pool

# Setup test database engine and session maker
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=False,
    poolclass=pool.NullPool
)
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Mock Redis client for rate limiting and cache tests
class MockRedis:
    def __init__(self):
        self.data = {}

    async def get(self, key: str):
        return self.data.get(key)

    async def set(self, key: str, value: str, ex=None):
        self.data[key] = str(value)
        return True

    async def keys(self, pattern: str):
        import fnmatch
        return [k for k in self.data.keys() if fnmatch.fnmatch(k, pattern)]

    async def delete(self, *keys: str):
        count = 0
        for k in keys:
            if k in self.data:
                del self.data[k]
                count += 1
        return count

    def pipeline(self, transaction=True):
        return MockPipeline(self)

class MockPipeline:
    def __init__(self, mock_redis: MockRedis):
        self.redis = mock_redis
        self.commands = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def incr(self, key: str):
        self.commands.append(("incr", key))

    def expire(self, key: str, window: int):
        self.commands.append(("expire", key, window))

    async def execute(self):
        for cmd in self.commands:
            if cmd[0] == "incr":
                key = cmd[1]
                val = int(self.redis.data.get(key, 0)) + 1
                self.redis.data[key] = str(val)
        self.commands = []

# Instantiate mock Redis client and monkeypatch dependencies module
mock_redis_client = MockRedis()
app.core.dependencies.redis_client = mock_redis_client

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def override_get_redis():
    return mock_redis_client

# Apply global overrides
fastapi_app.dependency_overrides[get_db] = override_get_db
fastapi_app.dependency_overrides[get_redis] = override_get_redis

@pytest.fixture(scope="session", autouse=True)
async def initialize_test_database():
    # Drop all tables and recreate them in the test database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    
    await engine.dispose()

@pytest.fixture(autouse=True)
async def seed_user():
    """Ensure the standard mock user exists in the SQLite database before every test."""
    async with async_session_maker() as session:
        user_id = uuid.UUID("4c02283e-a89e-4ff6-8c46-9c46e3ea86bf")
        user = await session.get(User, user_id)
        if not user:
            user = User(
                id=user_id,
                email="test_user@example.com",
                role="User"
            )
            session.add(user)
            await session.commit()

@pytest.fixture
def mock_user() -> User:
    from datetime import datetime
    return User(
        id=uuid.UUID("4c02283e-a89e-4ff6-8c46-9c46e3ea86bf"),
        email="test_user@example.com",
        role="User",
        created_at=datetime.utcnow()
    )

@pytest.fixture
async def client(mock_user: User) -> AsyncGenerator[AsyncClient, None]:
    async def override_current_user():
        return mock_user

    fastapi_app.dependency_overrides[get_current_user] = override_current_user
    
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
        yield ac
        
    # Keep global overrides intact, only clean temporary route overrides
    if get_current_user in fastapi_app.dependency_overrides:
        del fastapi_app.dependency_overrides[get_current_user]

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
