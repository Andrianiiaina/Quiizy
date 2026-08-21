"""Tests d'intégration contenus + fichiers.
Lancer avec : docker compose exec backend pytest tests/test_contents.py
"""
import sqlalchemy as sa
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


_USER = {"email": "content-user@test.com", "password": "password123", "first_name": "Content", "last_name": "User"}


async def _login(client: AsyncClient, user: dict) -> None:
    await client.post("/api/v1/auth/register", json=user)
    await client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})

async def _create_course(client: AsyncClient, title: str = "Test Course") -> dict:
    r = await client.post("/api/v1/courses", json={"title": title})
    assert r.status_code == 201
    return r.json()


@pytest.mark.usefixtures("clean_db")
class TestTextContent:
    async def test_create_text_content(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER)
        course = await _create_course(auth_client)
        r = await auth_client.post(f"/api/v1/courses/{course['id']}/contents", json={
            "type": "TEXT",
            "title": "Introduction",
            "text_content": "Bienvenue dans ce cours.",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["type"] == "TEXT"
        assert data["text_content"] == "Bienvenue dans ce cours."
        assert data["position"] == 0

    async def test_text_content_requires_text(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER)
        course = await _create_course(auth_client)
        r = await auth_client.post(f"/api/v1/courses/{course['id']}/contents", json={
            "type": "TEXT", "title": "Bad", "text_content": None,
        })
        assert r.status_code == 422

    async def test_list_contents_ordered_by_position(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER)
        course = await _create_course(auth_client)
        for i in range(3):
            await auth_client.post(f"/api/v1/courses/{course['id']}/contents", json={
                "type": "TEXT", "title": f"Section {i}", "text_content": "...",
            })
        r = await auth_client.get(f"/api/v1/courses/{course['id']}/contents")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 3
        assert [c["position"] for c in items] == [0, 1, 2]

    async def test_reorder_contents(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER)
        course = await _create_course(auth_client)
        ids = []
        for i in range(3):
            r = await auth_client.post(f"/api/v1/courses/{course['id']}/contents", json={
                "type": "TEXT", "title": f"Section {i}", "text_content": "...",
            })
            ids.append(r.json()["id"])
        # Reverse order
        reorder_payload = [{"id": ids[2], "position": 0}, {"id": ids[1], "position": 1}, {"id": ids[0], "position": 2}]
        r = await auth_client.patch(f"/api/v1/courses/{course['id']}/contents/reorder", json=reorder_payload)
        assert r.status_code == 204
        r = await auth_client.get(f"/api/v1/courses/{course['id']}/contents")
        items = r.json()
        assert items[0]["id"] == ids[2]


@pytest.mark.usefixtures("clean_db")
class TestWebLinkContent:
    async def test_create_weblink_content(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER)
        course = await _create_course(auth_client)
        r = await auth_client.post(f"/api/v1/courses/{course['id']}/contents", json={
            "type": "WEB_LINK",
            "title": "Doc officielle",
            "external_url": "https://fastapi.tiangolo.com",
        })
        assert r.status_code == 201
        assert r.json()["external_url"] == "https://fastapi.tiangolo.com"

    async def test_weblink_must_be_https(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER)
        course = await _create_course(auth_client)
        r = await auth_client.post(f"/api/v1/courses/{course['id']}/contents", json={
            "type": "WEB_LINK", "title": "Insecure", "external_url": "http://example.com",
        })
        assert r.status_code == 422
        assert r.json()["code"] == "INVALID_URL"


@pytest.mark.usefixtures("clean_db")
class TestContentOwnership:
    async def test_non_owner_cannot_delete_content(self, auth_client: AsyncClient) -> None:
        _USER_B = {"email": "content-b@test.com", "password": "password123", "first_name": "B", "last_name": "B"}
        await _login(auth_client, _USER)
        course = await _create_course(auth_client)
        create_r = await auth_client.post(f"/api/v1/courses/{course['id']}/contents", json={
            "type": "TEXT", "title": "Mine", "text_content": "content",
        })
        content_id = create_r.json()["id"]
        await auth_client.post("/api/v1/auth/logout")
        await _login(auth_client, _USER_B)
        r = await auth_client.delete(f"/api/v1/contents/{content_id}")
        assert r.status_code == 403
