"""Tests d'intégration assignments + enrollments.
Lancer avec : docker compose exec backend pytest tests/test_assignments.py
"""
import sqlalchemy as sa
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

_ADMIN  = {"email": "asgn-admin@test.com",  "password": "password123", "first_name": "Admin", "last_name": "X"}
_USER_A = {"email": "asgn-usera@test.com",  "password": "password123", "first_name": "User",  "last_name": "A"}
_USER_B = {"email": "asgn-userb@test.com",  "password": "password123", "first_name": "User",  "last_name": "B"}


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


@pytest.mark.usefixtures("clean_all")
class TestAssignmentPermissions:
    async def test_non_admin_cannot_create_assignment(self, auth_client: AsyncClient) -> None:
        import uuid
        await _register(auth_client, _USER_A)
        await _login(auth_client, _USER_A)
        r = await auth_client.post("/api/v1/assignments", json={
            "user_id": str(uuid.uuid4()), "target_type": "COURSE", "target_id": str(uuid.uuid4()),
        })
        assert r.status_code == 403

    async def test_non_admin_cannot_list_assignments(self, auth_client: AsyncClient) -> None:
        await _register(auth_client, _USER_A)
        await _login(auth_client, _USER_A)
        r = await auth_client.get("/api/v1/assignments")
        assert r.status_code == 403

    async def test_unauthenticated_cannot_create_assignment(self, auth_client: AsyncClient) -> None:
        import uuid
        r = await auth_client.post("/api/v1/assignments", json={
            "user_id": str(uuid.uuid4()), "target_type": "COURSE", "target_id": str(uuid.uuid4()),
        })
        assert r.status_code == 401


@pytest.mark.usefixtures("clean_all")
class TestAssignmentCRUD:
    async def test_admin_assigns_course_creates_enrollment(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        course_id = (await auth_client.post("/api/v1/courses", json={"title": "Course"})).json()["id"]

        await _register(auth_client, _USER_A)
        user_a_id = await _get_user_id(db_session, _USER_A["email"])

        r = await auth_client.post("/api/v1/assignments", json={
            "user_id": user_a_id, "target_type": "COURSE", "target_id": course_id,
        })
        assert r.status_code == 201
        assert r.json()["target_type"] == "COURSE"
        assert r.json()["user_id"] == user_a_id

        # Enrollment created — admin sees it in the list
        enrollments = (await auth_client.get("/api/v1/enrollments")).json()
        assert any(e["course_id"] == course_id for e in enrollments)

    async def test_assignment_to_nonexistent_course_fails(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        import uuid
        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        await _register(auth_client, _USER_A)
        user_a_id = await _get_user_id(db_session, _USER_A["email"])

        r = await auth_client.post("/api/v1/assignments", json={
            "user_id": user_a_id, "target_type": "COURSE", "target_id": str(uuid.uuid4()),
        })
        assert r.status_code == 404

    async def test_admin_can_list_all_assignments(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        r = await auth_client.get("/api/v1/assignments")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


@pytest.mark.usefixtures("clean_all")
class TestEnrollmentIsolation:
    async def test_user_sees_only_own_enrollments(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        course_id = (await auth_client.post("/api/v1/courses", json={"title": "Course"})).json()["id"]

        await _register(auth_client, _USER_A)
        await _register(auth_client, _USER_B)
        user_a_id = await _get_user_id(db_session, _USER_A["email"])

        # Assign only to user A
        await auth_client.post("/api/v1/assignments", json={
            "user_id": user_a_id, "target_type": "COURSE", "target_id": course_id,
        })

        await _logout(auth_client)
        await _login(auth_client, _USER_B)
        r = await auth_client.get("/api/v1/enrollments")
        assert r.status_code == 200
        assert r.json() == []

    async def test_user_cannot_access_other_user_enrollment(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        course_id = (await auth_client.post("/api/v1/courses", json={"title": "Course"})).json()["id"]

        await _register(auth_client, _USER_A)
        await _register(auth_client, _USER_B)
        user_a_id = await _get_user_id(db_session, _USER_A["email"])

        await auth_client.post("/api/v1/assignments", json={
            "user_id": user_a_id, "target_type": "COURSE", "target_id": course_id,
        })
        # Get enrollment_id via admin
        enrollments = (await auth_client.get("/api/v1/enrollments")).json()
        enrollment_id = enrollments[0]["id"]

        # User B cannot fetch user A's enrollment
        await _logout(auth_client)
        await _login(auth_client, _USER_B)
        r = await auth_client.get(f"/api/v1/enrollments/{enrollment_id}")
        assert r.status_code == 404  # deliberate opacity — not 403
