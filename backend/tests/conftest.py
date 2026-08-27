import sqlalchemy as sa
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import get_db
from app.main import app

# ── Client léger (sans DB) pour les tests unitaires ───────────────────────────

@pytest.fixture
async def client() -> AsyncClient:  # type: ignore[return]
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── Fixtures d'intégration — nécessitent PostgreSQL ───────────────────────────

_test_engine = create_async_engine(settings.DATABASE_URL, echo=False)
_TestSession = async_sessionmaker(_test_engine, expire_on_commit=False)


@pytest.fixture
async def db_session() -> AsyncSession:  # type: ignore[return]
    async with _TestSession() as session:
        yield session


@pytest.fixture
async def auth_client(db_session: AsyncSession) -> AsyncClient:  # type: ignore[return]
    """Client injectant la session de test — pour les tests d'intégration auth."""
    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def clean_users() -> None:  # type: ignore[return]
    """Purge les tables auth après chaque test qui l'utilise."""
    yield
    async with _TestSession() as session:
        await session.execute(sa.text("DELETE FROM refresh_tokens"))
        await session.execute(sa.text("DELETE FROM users"))
        await session.commit()


@pytest.fixture
async def clean_all() -> None:  # type: ignore[return]
    """Purge toutes les tables dans l'ordre correct (TRUNCATE sans CASCADE grâce à la liste complète)."""
    yield
    async with _TestSession() as session:
        await session.execute(sa.text(
            "TRUNCATE TABLE "
            "quiz_answers, quiz_attempts, content_progress, enrollments, assignments, "
            "quiz_generation_jobs, quiz_options, quiz_questions, quizzes, "
            "learning_path_courses, learning_paths, course_contents, file_assets, "
            "courses, categories, refresh_tokens, users"
        ))
        await session.commit()


@pytest.fixture
async def clean_db() -> None:  # type: ignore[return]
    """Purge toutes les tables métier (respecte l'ordre des FK)."""
    yield
    async with _TestSession() as session:
        await session.execute(sa.text("DELETE FROM courses"))
        await session.execute(sa.text("DELETE FROM categories"))
        await session.execute(sa.text("DELETE FROM users"))  # cascade → refresh_tokens
        await session.commit()
