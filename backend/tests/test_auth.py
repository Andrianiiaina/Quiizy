"""Tests d'intégration auth — nécessitent PostgreSQL.
Lancer avec : docker compose exec backend pytest tests/test_auth.py
"""
import pytest
from httpx import AsyncClient

_USER = {
    "email": "auth-test@example.com",
    "password": "securepass123",
    "first_name": "Test",
    "last_name": "User",
}


@pytest.mark.usefixtures("clean_users")
class TestRegister:
    async def test_success(self, auth_client: AsyncClient) -> None:
        r = await auth_client.post("/api/v1/auth/register", json=_USER)
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == _USER["email"]
        assert data["role"] == "USER"
        assert "password_hash" not in data

    async def test_duplicate_email(self, auth_client: AsyncClient) -> None:
        await auth_client.post("/api/v1/auth/register", json=_USER)
        r = await auth_client.post("/api/v1/auth/register", json=_USER)
        assert r.status_code == 409
        assert r.json()["code"] == "EMAIL_ALREADY_EXISTS"

    async def test_invalid_email(self, auth_client: AsyncClient) -> None:
        r = await auth_client.post(
            "/api/v1/auth/register", json={**_USER, "email": "not-an-email"}
        )
        assert r.status_code == 422

    async def test_short_password(self, auth_client: AsyncClient) -> None:
        r = await auth_client.post(
            "/api/v1/auth/register", json={**_USER, "password": "short"}
        )
        assert r.status_code == 422


@pytest.mark.usefixtures("clean_users")
class TestLogin:
    async def test_success_sets_cookies(self, auth_client: AsyncClient) -> None:
        await auth_client.post("/api/v1/auth/register", json=_USER)
        r = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": _USER["email"], "password": _USER["password"]},
        )
        assert r.status_code == 200
        assert "access_token" in r.cookies
        assert "refresh_token" in r.cookies
        assert r.json()["email"] == _USER["email"]

    async def test_wrong_password(self, auth_client: AsyncClient) -> None:
        await auth_client.post("/api/v1/auth/register", json=_USER)
        r = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": _USER["email"], "password": "wrongpassword"},
        )
        assert r.status_code == 401
        assert r.json()["code"] == "INVALID_CREDENTIALS"

    async def test_unknown_user(self, auth_client: AsyncClient) -> None:
        r = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "anypassword"},
        )
        assert r.status_code == 401
        assert r.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.usefixtures("clean_users")
class TestMe:
    async def test_me_authenticated(self, auth_client: AsyncClient) -> None:
        await auth_client.post("/api/v1/auth/register", json=_USER)
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": _USER["email"], "password": _USER["password"]},
        )
        r = await auth_client.get("/api/v1/auth/me")
        assert r.status_code == 200
        assert r.json()["email"] == _USER["email"]

    async def test_me_unauthenticated(self, auth_client: AsyncClient) -> None:
        r = await auth_client.get("/api/v1/auth/me")
        assert r.status_code == 401
        assert r.json()["code"] == "NOT_AUTHENTICATED"


@pytest.mark.usefixtures("clean_users")
class TestLogout:
    async def test_logout_clears_session(self, auth_client: AsyncClient) -> None:
        await auth_client.post("/api/v1/auth/register", json=_USER)
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": _USER["email"], "password": _USER["password"]},
        )
        r_logout = await auth_client.post("/api/v1/auth/logout")
        assert r_logout.status_code == 204
        # Me doit retourner 401 après logout
        r_me = await auth_client.get("/api/v1/auth/me")
        assert r_me.status_code == 401
