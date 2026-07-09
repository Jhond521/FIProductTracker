import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.accounts.models import User
from app.accounts.security import create_session_token
from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app


@pytest_asyncio.fixture
async def async_client():
    # SQLite in-memory for CI/local test speed — Postgres-specific behavior
    # (e.g. UUID type nuances) is still exercised via docker-compose locally,
    # this fixture is for fast logic/wiring tests only.
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # stashed so tests/fixtures can create rows directly without going through the API
        client.session_factory = test_session_factory
        yield client

    app.dependency_overrides.clear()
    await test_engine.dispose()


async def create_test_user(session_factory, *, email: str = "test@example.com") -> User:
    user = User(google_sub=f"google-{uuid.uuid4()}", email=email, name="Test User")
    async with session_factory() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def authenticated_client(async_client):
    """An async_client with a valid session cookie for a freshly-created user.

    The user is exposed as `.current_user` for assertions.
    """
    user = await create_test_user(async_client.session_factory)
    token = create_session_token(user.id)
    async_client.cookies.set(settings.session_cookie_name, token)
    async_client.current_user = user
    yield async_client
