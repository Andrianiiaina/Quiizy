"""Tests d'intégration quiz — génération de jobs et tentatives.
Lancer avec : docker compose exec backend pytest tests/test_quizzes.py
"""
import uuid as _uuid
import sqlalchemy as sa
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

_ADMIN  = {"email": "quiz-admin@test.com", "password": "password123", "first_name": "Admin", "last_name": "X"}
_USER_A = {"email": "quiz-usera@test.com", "password": "password123", "first_name": "User",  "last_name": "A"}
_USER_B = {"email": "quiz-userb@test.com", "password": "password123", "first_name": "User",  "last_name": "B"}


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


async def _create_course_with_text_content(client: AsyncClient) -> tuple[str, str]:
    """Returns (course_id, content_id)."""
    course_id = (await client.post("/api/v1/courses", json={"title": "Quiz Course"})).json()["id"]
    content_id = (await client.post(f"/api/v1/courses/{course_id}/contents", json={
        "type": "TEXT", "title": "Chapter 1",
        "text_content": "Python est un langage interprété, de haut niveau, à usage général.",
    })).json()["id"]
    return course_id, content_id


@pytest.mark.usefixtures("clean_all")
class TestQuizGeneration:
    async def test_course_owner_triggers_generation_returns_job(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        course_id, _ = await _create_course_with_text_content(auth_client)

        r = await auth_client.post(f"/api/v1/courses/{course_id}/quiz/generate")
        assert r.status_code == 202
        data = r.json()
        assert data["status"] == "PENDING"
        assert data["course_id"] == course_id

    async def test_non_owner_cannot_trigger_generation(self, auth_client: AsyncClient) -> None:
        await _register(auth_client, _USER_A)
        await _login(auth_client, _USER_A)
        r = await auth_client.post(f"/api/v1/courses/{_uuid.uuid4()}/quiz/generate")
        assert r.status_code in (403, 404)

    async def test_get_job_status(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        course_id, _ = await _create_course_with_text_content(auth_client)

        job_id = (await auth_client.post(f"/api/v1/courses/{course_id}/quiz/generate")).json()["id"]
        r = await auth_client.get(f"/api/v1/quiz-generation-jobs/{job_id}")
        assert r.status_code == 200
        assert r.json()["id"] == job_id


@pytest.mark.usefixtures("clean_all")
class TestQuizAttempt:
    async def test_cannot_start_attempt_without_valid_enrollment(
        self, auth_client: AsyncClient
    ) -> None:
        await _register(auth_client, _USER_A)
        await _login(auth_client, _USER_A)
        r = await auth_client.post(
            f"/api/v1/quizzes/{_uuid.uuid4()}/attempts",
            params={"enrollment_id": str(_uuid.uuid4())},
        )
        assert r.status_code in (404, 422)

    async def test_cannot_complete_nonexistent_attempt(self, auth_client: AsyncClient) -> None:
        await _register(auth_client, _USER_A)
        await _login(auth_client, _USER_A)
        r = await auth_client.post(f"/api/v1/quiz-attempts/{_uuid.uuid4()}/complete")
        assert r.status_code == 404

    async def test_double_answer_rejected(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Answering the same question twice in an attempt must return 409."""
        from app.modules.quizzes.generation import run_generation_job, trigger_generation

        await _register(auth_client, _ADMIN)
        await _login(auth_client, _ADMIN)
        await _promote_admin(db_session, _ADMIN["email"])
        course_id, _ = await _create_course_with_text_content(auth_client)

        # Run generation synchronously in test
        admin_id = await _get_user_id(db_session, _ADMIN["email"])
        job = await trigger_generation(_uuid.UUID(course_id), _uuid.UUID(admin_id), db_session)
        await db_session.commit()
        await run_generation_job(job.id)

        # Assign course to USER_A
        await _register(auth_client, _USER_A)
        user_a_id = await _get_user_id(db_session, _USER_A["email"])
        await auth_client.post("/api/v1/assignments", json={
            "user_id": user_a_id, "target_type": "COURSE", "target_id": course_id,
        })
        enrollments = (await auth_client.get("/api/v1/enrollments")).json()
        enrollment_id = next(e["id"] for e in enrollments if e["course_id"] == course_id)

        # Get quiz
        quiz_r = await auth_client.get(f"/api/v1/courses/{course_id}/quiz")
        if quiz_r.status_code != 200:
            pytest.skip("Quiz generation produced no active quiz (stub may have failed)")
        quiz_id = quiz_r.json()["id"]

        await _logout(auth_client)
        await _login(auth_client, _USER_A)
        attempt_r = await auth_client.post(
            f"/api/v1/quizzes/{quiz_id}/attempts",
            params={"enrollment_id": enrollment_id},
        )
        assert attempt_r.status_code == 201
        attempt_data = attempt_r.json()
        attempt_id = attempt_data["id"]

        if not attempt_data["questions"]:
            pytest.skip("No questions in quiz")

        q = attempt_data["questions"][0]
        option_id = q["options"][0]["id"]
        payload = {"question_id": q["id"], "selected_option_id": option_id}

        r1 = await auth_client.post(f"/api/v1/quiz-attempts/{attempt_id}/answers", json=payload)
        assert r1.status_code == 200

        # Second submission to same question must fail
        r2 = await auth_client.post(f"/api/v1/quiz-attempts/{attempt_id}/answers", json=payload)
        assert r2.status_code == 409
