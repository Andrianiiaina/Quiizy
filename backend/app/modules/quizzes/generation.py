"""Quiz generation pipeline — stub implementation.
Replace the _run_stub_generation function with real AI API calls.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.modules.contents.models import ContentType
from app.modules.contents.repository import ContentRepository
from app.modules.quizzes.models import (
    JobStatus, Quiz, QuizGenerationJob, QuizOption, QuizQuestion, QuizStatus,
)
from app.modules.quizzes.repository import QuizRepository


async def trigger_generation(course_id: uuid.UUID, requested_by: uuid.UUID, db: AsyncSession) -> QuizGenerationJob:
    job = QuizGenerationJob(course_id=course_id, requested_by=requested_by)
    db.add(job)
    await db.flush()
    await db.refresh(job)
    await db.commit()
    return job


async def run_generation_job(job_id: uuid.UUID) -> None:
    """Runs in a BackgroundTask — creates its own DB session."""
    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        repo = QuizRepository(db)
        job = await repo.get_job(job_id)
        if not job:
            return

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            await _run_stub_generation(job, db, repo)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)[:500]
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

    await engine.dispose()


async def _run_stub_generation(job: QuizGenerationJob, db: AsyncSession, repo: QuizRepository) -> None:
    contents = await ContentRepository(db).list_for_course(job.course_id)
    text_contents = [c for c in contents if c.type == ContentType.TEXT and c.text_content]

    if not text_contents:
        raise ValueError("No TEXT contents found. Add text content before generating a quiz.")

    # Archive previous active quiz
    existing = await repo.get_active_for_course(job.course_id)
    if existing:
        existing.status = QuizStatus.ARCHIVED

    version = await repo.get_latest_version(job.course_id) + 1
    quiz = Quiz(course_id=job.course_id, version=version, status=QuizStatus.DRAFT, question_count=0)
    db.add(quiz)
    await db.flush()

    question_count = 0
    for i, content in enumerate(text_contents[:5]):
        question = QuizQuestion(
            quiz_id=quiz.id,
            question=f"Concernant « {content.title} » : quelle affirmation est correcte ?",
            explanation=f"Cette question porte sur le contenu « {content.title} ». La première option résume l'idée principale.",
            source_content_id=content.id,
            source_reference=content.title,
            position=i,
        )
        db.add(question)
        await db.flush()

        options_text = [
            f"Le contenu « {content.title} » présente l'idée principale du module.",
            "Cette notion n'est pas abordée dans le cours.",
            "L'affirmation inverse est vraie.",
            "Cette option n'est pas liée au sujet.",
        ]
        for j, text in enumerate(options_text):
            db.add(QuizOption(question_id=question.id, text=text, is_correct=(j == 0), position=j))

        question_count += 1

    quiz.question_count = question_count
    quiz.status = QuizStatus.ACTIVE
    quiz.generated_at = datetime.now(timezone.utc)
    await db.flush()
