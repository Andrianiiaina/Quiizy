"""Tests d'intégration progression des contenus.
Lancer avec : docker compose exec backend pytest tests/test_progress.py
"""
import sqlalchemy as sa
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

_ADMIN  = {"email": "prog-admin@test.com", "password": "password123", "first_name": "Admin", "last_name": "X"}
_USER_A = {"email": "prog-usera@test.com", "password": "password123", "first_name": "User",  "last_name": "A"}
_USER_B = {"email": "prog-userb@test.com", "password": "password123", "first_name": "User",  "last_name": "B"}


async def _register(client: AsyncClient, user: dict) -> None:
    await client.post("/api/v1/auth/register", json=user)


async def _login(client: AsyncClient, user: dict) -> None:
    await client.post("/api/v1/auth/login", json={"email": user["email"], "password": user["password"]})


async def _logout(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/logout")


async def _promote_admin(session: AsyncSession, email: str) -> None:
    await session.execute(sa.text("UPDATE users SET role = 'ADMIN' WHERE email = :email"), {"email": email})
    await session.commit()


async def _get_user_id(session: AsyncSession, email: str) -> str:
    r = await session.execute(sa.text("SELECT id FROM users WHERE email = :email"), {"email": email})
    return str(r.scalar_one())


async def _setup_enrollment(
    client: AsyncClient, session: AsyncSession, learner_email: str
) -> tuple[str, str, str]:
    """Create course with one TEXT content, assign to learner. Returns (enrollment_id, content_id, course_id)."""
    course_r = await client.post("/api/v1/courses", json={"title": "Progress Test Course"})
    course_id = course_r.json()["id"]

    content_r = await client.post(f"/api/v1/courses/{course_id}/contents", json={
        "type": "TEXT", "title": "Chapter 1", "text_content": "Content body.",
    })
    content_id = content_r.json()["id"]

    user_id = await _get_user_id(session, learner_email)
    await client.post("/api/v1/assignments", json={
        "user_id": user_id, "target_type": "COURSE", "target_id": course_id,
    })

    # Get enrollment from admin's list
    enrollments = (await client.get("/api/v1/enrollments")).json()
    enrollment = next(e for e in enrollments if e["course_id"] == course_id)
    return enrollment["id"], content_id, course_id


@pytest.mark.usefixtures("clean_all")
class TestContentProgress:
    async def test_user_can_update_own_content_progress(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        await _register(auth_client, _USER_A)
        enrollment_id, content_id, _ = await _setup_enrollment(auth_client, db_session, _USER_A["email"])

        await _logout(auth_client)
        await _login(auth_client, _USER_A)
        r = await auth_client.post(
            f"/api/v1/enrollments/{enrollment_id}/contents/{content_id}/progress",
            json={"status": "IN_PROGRESS", "progress_percent": 50},
        )
        assert r.status_code == 200
        assert r.json()["progress_percent"] == 50
        assert r.json()["status"] == "IN_PROGRESS"

    async def test_completing_content_updates_enrollment(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        await _register(auth_client, _USER_A)
        enrollment_id, content_id, _ = await _setup_enrollment(auth_client, db_session, _USER_A["email"])

        await _logout(auth_client)
        await _login(auth_client, _USER_A)
        await auth_client.post(
            f"/api/v1/enrollments/{enrollment_id}/contents/{content_id}/progress",
            json={"status": "COMPLETED", "progress_percent": 100},
        )

        # Enrollment status should have moved to IN_PROGRESS (or COMPLETED for single-content course)
        enrollment = (await auth_client.get(f"/api/v1/enrollments/{enrollment_id}")).json()
        assert enrollment["status"] in ("IN_PROGRESS", "COMPLETED")
        assert enrollment["progress_percent"] > 0

    async def test_user_cannot_update_other_user_progress(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        await _register(auth_client, _USER_A)
        await _register(auth_client, _USER_B)
        enrollment_id, content_id, _ = await _setup_enrollment(auth_client, db_session, _USER_A["email"])

        # User B tries to write progress on User A's enrollment
        await _logout(auth_client)
        await _login(auth_client, _USER_B)
        r = await auth_client.post(
            f"/api/v1/enrollments/{enrollment_id}/contents/{content_id}/progress",
            json={"status": "COMPLETED", "progress_percent": 100},
        )
        assert r.status_code == 403

    async def test_user_cannot_read_other_user_progress(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        await _register(auth_client, _USER_A)
        await _register(auth_client, _USER_B)
        enrollment_id, _, _ = await _setup_enrollment(auth_client, db_session, _USER_A["email"])

        await _logout(auth_client)
        await _login(auth_client, _USER_B)
        r = await auth_client.get(f"/api/v1/enrollments/{enrollment_id}/progress")
        assert r.status_code == 404  # deliberate opacity
