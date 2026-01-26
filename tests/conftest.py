"""Pytest configuration and fixtures."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import generate_api_key, hash_api_key
from app.db.base import Base
from app.db.models import User
from app.main import app

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def sync_client() -> TestClient:
    """Synchronous test client fixture."""
    return TestClient(app)


@pytest.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user with API key."""
    api_key = generate_api_key()
    user = User(
        id=uuid4(),
        email="test@example.com",
        api_key_hash=hash_api_key(api_key),
        tier="free",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Store API key on user for testing
    user._api_key = api_key  # type: ignore
    return user


@pytest.fixture
def test_api_key(test_user: User) -> str:
    """Get test user's API key."""
    return test_user._api_key  # type: ignore


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test HTTP client."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    from app.db.session import get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Keep original client fixture for backward compatibility
@pytest.fixture
def client() -> TestClient:
    """Test client fixture."""
    return TestClient(app)
