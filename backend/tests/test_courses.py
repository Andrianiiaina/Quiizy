"""Tests d'intégration cours + catégories.
Lancer avec : docker compose exec backend pytest tests/test_courses.py
"""
import sqlalchemy as sa
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

_USER_A = {"email": "user-a@test.com", "password": "password123", "first_name": "User", "last_name": "A"}
_USER_B = {"email": "user-b@test.com", "password": "password123", "first_name": "User", "last_name": "B"}
_ADMIN  = {"email": "admin@test.com",  "password": "password123", "first_name": "Admin", "last_name": "X"}


async def _login(client: AsyncClient, user: dict) -> None:
    await client.post("/api/v1/auth/register", json=user)
    await client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


async def _logout(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/logout")


async def _promote_admin(session: AsyncSession, email: str) -> None:
    await session.execute(
        sa.text("UPDATE users SET role = 'ADMIN' WHERE email = :email"), {"email": email}
    )
    await session.commit()


@pytest.mark.usefixtures("clean_db")
class TestCategoryAdmin:
    async def test_admin_creates_category(self, auth_client: AsyncClient, db_session: AsyncSession) -> None:
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        r = await auth_client.post("/api/v1/categories", json={"name": "Python"})
        assert r.status_code == 201
        assert r.json()["name"] == "Python"

    async def test_user_can_create_category(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER_A)
        r = await auth_client.post("/api/v1/categories", json={"name": "Dev"})
        assert r.status_code == 201
        assert r.json()["name"] == "Dev"

    async def test_user_cannot_update_category(self, auth_client: AsyncClient, db_session: AsyncSession) -> None:
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        cat_id = (await auth_client.post("/api/v1/categories", json={"name": "ToEdit"})).json()["id"]
        await _logout(auth_client)

        await _login(auth_client, _USER_A)
        r = await auth_client.patch(f"/api/v1/categories/{cat_id}", json={"name": "Hacked"})
        assert r.status_code == 403

    async def test_user_cannot_delete_category(self, auth_client: AsyncClient, db_session: AsyncSession) -> None:
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        cat_id = (await auth_client.post("/api/v1/categories", json={"name": "ToDelete"})).json()["id"]
        await _logout(auth_client)

        await _login(auth_client, _USER_A)
        r = await auth_client.delete(f"/api/v1/categories/{cat_id}")
        assert r.status_code == 403

    async def test_duplicate_category_rejected(self, auth_client: AsyncClient, db_session: AsyncSession) -> None:
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        await auth_client.post("/api/v1/categories", json={"name": "Unique"})
        r = await auth_client.post("/api/v1/categories", json={"name": "Unique"})
        assert r.status_code == 409


@pytest.mark.usefixtures("clean_db")
class TestCourseCRUD:
    async def test_create_course_sets_owner(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER_A)
        r = await auth_client.post("/api/v1/courses", json={"title": "My Course"})
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "My Course"
        assert data["status"] == "DRAFT"
        assert data["owner_id"] is not None

    async def test_list_shows_own_draft_and_published_courses(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER_A)
        await auth_client.post("/api/v1/courses", json={"title": "Draft Course"})
        r = await auth_client.get("/api/v1/courses")
        assert r.status_code == 200
        assert r.json()["total"] >= 1


@pytest.mark.usefixtures("clean_db")
class TestCourseOwnership:
    async def test_user_b_cannot_edit_user_a_course(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER_A)
        create_r = await auth_client.post("/api/v1/courses", json={"title": "A's Course"})
        course_id = create_r.json()["id"]
        await _logout(auth_client)

        await _login(auth_client, _USER_B)
        r = await auth_client.patch(f"/api/v1/courses/{course_id}", json={"title": "Hacked"})
        assert r.status_code == 404  # DRAFT non visible pour un non-owner — opacité délibérée

    async def test_user_b_cannot_delete_user_a_course(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER_A)
        create_r = await auth_client.post("/api/v1/courses", json={"title": "A's Course 2"})
        course_id = create_r.json()["id"]
        await _logout(auth_client)

        await _login(auth_client, _USER_B)
        r = await auth_client.delete(f"/api/v1/courses/{course_id}")
        assert r.status_code == 404  # DRAFT non visible pour un non-owner — opacité délibérée

    async def test_admin_can_edit_any_course(self, auth_client: AsyncClient, db_session: AsyncSession) -> None:
        await _login(auth_client, _USER_A)
        create_r = await auth_client.post("/api/v1/courses", json={"title": "A's Course 3"})
        course_id = create_r.json()["id"]
        await _logout(auth_client)

        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        r = await auth_client.patch(f"/api/v1/courses/{course_id}", json={"title": "Admin Edited"})
        assert r.status_code == 200
        assert r.json()["title"] == "Admin Edited"

    async def test_draft_invisible_to_other_users(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER_A)
        create_r = await auth_client.post("/api/v1/courses", json={"title": "Hidden Draft"})
        course_id = create_r.json()["id"]
        await _logout(auth_client)

        await _login(auth_client, _USER_B)
        r = await auth_client.get(f"/api/v1/courses/{course_id}")
        assert r.status_code == 404


@pytest.mark.usefixtures("clean_db")
class TestCourseStatusTransitions:
    async def test_publish_draft_course(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER_A)
        create_r = await auth_client.post("/api/v1/courses", json={"title": "To Publish"})
        course_id = create_r.json()["id"]
        r = await auth_client.patch(f"/api/v1/courses/{course_id}/publish")
        assert r.status_code == 200
        assert r.json()["status"] == "PUBLISHED"

    async def test_cannot_publish_already_published(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER_A)
        create_r = await auth_client.post("/api/v1/courses", json={"title": "Already Published"})
        course_id = create_r.json()["id"]
        await auth_client.patch(f"/api/v1/courses/{course_id}/publish")
        r = await auth_client.patch(f"/api/v1/courses/{course_id}/publish")
        assert r.status_code == 409
        assert r.json()["code"] == "INVALID_STATUS_TRANSITION"

    async def test_archive_published_course(self, auth_client: AsyncClient) -> None:
        await _login(auth_client, _USER_A)
        create_r = await auth_client.post("/api/v1/courses", json={"title": "To Archive"})
        course_id = create_r.json()["id"]
        await auth_client.patch(f"/api/v1/courses/{course_id}/publish")
        r = await auth_client.patch(f"/api/v1/courses/{course_id}/archive")
        assert r.status_code == 200
        assert r.json()["status"] == "ARCHIVED"
