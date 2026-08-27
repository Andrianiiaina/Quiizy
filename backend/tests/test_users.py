"""Tests d'intégration users admin.
Lancer avec : docker compose exec backend pytest tests/test_users.py
"""
import sqlalchemy as sa
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

_ADMIN = {"email": "users-admin@test.com", "password": "password123", "first_name": "Admin", "last_name": "X"}
_USER  = {"email": "users-user@test.com",  "password": "password123", "first_name": "User",  "last_name": "Y"}


async def _login(client: AsyncClient, user: dict) -> None:
    await client.post("/api/v1/auth/register", json=user)
    await client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


async def _logout(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/logout")


async def _promote_admin(session: AsyncSession, email: str) -> None:
    await session.execute(sa.text("UPDATE users SET role = 'ADMIN' WHERE email = :email"), {"email": email})
    await session.commit()


@pytest.mark.usefixtures("clean_users")
class TestUsersAdmin:
    async def test_non_admin_cannot_list_users(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER)
        r = await auth_client.get("/api/v1/users")
        assert r.status_code == 403

    async def test_unauthenticated_cannot_list_users(self, auth_client: AsyncClient) -> None:
        r = await auth_client.get("/api/v1/users")
        assert r.status_code == 401

    async def test_admin_can_list_users(self, auth_client: AsyncClient, db_session: AsyncSession) -> None:
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        r = await auth_client.get("/api/v1/users")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert any(u["email"] == _ADMIN["email"] for u in data)

    async def test_admin_can_get_user_by_id(self, auth_client: AsyncClient, db_session: AsyncSession) -> None:
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        await _logout(auth_client)
        await _login(auth_client, _USER)
        user_id = (await auth_client.get("/api/v1/auth/me")).json()["id"]
        await _logout(auth_client)
        await auth_client.post("/api/v1/auth/login", json={"email": _ADMIN["email"], "password": _ADMIN["password"]})
        r = await auth_client.get(f"/api/v1/users/{user_id}")
        assert r.status_code == 200
        assert r.json()["email"] == _USER["email"]

    async def test_admin_get_unknown_user_returns_404(self, auth_client: AsyncClient, db_session: AsyncSession) -> None:
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        r = await auth_client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404
        assert r.json()["code"] == "USER_NOT_FOUND"
