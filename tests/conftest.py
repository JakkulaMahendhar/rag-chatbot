import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import settings
from app.main import app
from app.auth.router import _auth_rate_limiter

# Synchronous engine used only for test cleanup, kept separate from the
# app's async engine so teardown never has to share an event loop with
# TestClient's own async request handling.
_sync_engine = create_engine(settings.DATABASE_URL_SYNC)


@pytest.fixture(scope="session", autouse=True)
def _relax_auth_rate_limit():
    """
    Integration tests register/login many users from the same
    TestClient IP, which would otherwise trip the production
    rate limiter within a single test run.
    """

    _auth_rate_limiter.max_attempts = 10_000


@pytest.fixture(scope="session")
def client():

    with TestClient(app) as test_client:
        yield test_client


def _delete_user(user_id: int):

    with _sync_engine.begin() as conn:

        conn.execute(
            text("DELETE FROM documents WHERE user_id = :id"), {"id": user_id}
        )

        conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})


@pytest.fixture
def register_user(client):
    """
    Registers + logs in a fresh user for a single test.

    Returns a dict with id/email/password/token/headers.
    Cleans up the user (and any documents left owned by it)
    once the test finishes.
    """

    created_ids: list[int] = []

    def _create(password: str = "TestPassword123"):

        email = f"test-{uuid.uuid4().hex[:12]}@example.com"

        response = client.post(
            "/auth/register", json={"email": email, "password": password}
        )

        assert response.status_code == 200, response.text

        user_id = response.json()["id"]

        created_ids.append(user_id)

        login = client.post(
            "/auth/login", json={"email": email, "password": password}
        )

        assert login.status_code == 200, login.text

        token = login.json()["access_token"]

        return {
            "id": user_id,
            "email": email,
            "password": password,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
        }

    yield _create

    for user_id in created_ids:
        _delete_user(user_id)
