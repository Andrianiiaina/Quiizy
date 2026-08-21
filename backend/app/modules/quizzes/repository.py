import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.quizzes.models import (
    Quiz, QuizAttempt, QuizAnswer, QuizGenerationJob,
    QuizQuestion, QuizOption, QuizStatus,
)


class QuizRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_active_for_course(self, course_id: uuid.UUID) -> Quiz | None:
        return (await self._db.execute(
            select(Quiz).where(Quiz.course_id == course_id, Quiz.status == QuizStatus.ACTIVE)
        )).scalar_one_or_none()

    async def get_by_id(self, quiz_id: uuid.UUID) -> Quiz | None:
        return (await self._db.execute(select(Quiz).where(Quiz.id == quiz_id))).scalar_one_or_none()

    async def get_with_questions(self, quiz_id: uuid.UUID) -> Quiz | None:
        result = await self._db.execute(
            select(Quiz).options(
                selectinload(Quiz.questions).selectinload(QuizQuestion.options)
            ).where(Quiz.id == quiz_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_version(self, course_id: uuid.UUID) -> int:
        from sqlalchemy import func
        result = await self._db.execute(
            select(func.coalesce(func.max(Quiz.version), 0)).where(Quiz.course_id == course_id)
        )
        return result.scalar_one()

    async def get_job(self, job_id: uuid.UUID) -> QuizGenerationJob | None:
        return (await self._db.execute(select(QuizGenerationJob).where(QuizGenerationJob.id == job_id))).scalar_one_or_none()

    async def get_attempt(self, attempt_id: uuid.UUID) -> QuizAttempt | None:
        return (await self._db.execute(select(QuizAttempt).where(QuizAttempt.id == attempt_id))).scalar_one_or_none()

    async def get_open_attempt(self, user_id: uuid.UUID, quiz_id: uuid.UUID) -> QuizAttempt | None:
        return (await self._db.execute(
            select(QuizAttempt).where(
                QuizAttempt.user_id == user_id,
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.completed_at.is_(None),
            )
        )).scalar_one_or_none()

    async def get_attempts_for_enrollment(self, enrollment_id: uuid.UUID) -> list[QuizAttempt]:
        result = await self._db.execute(
            select(QuizAttempt).where(QuizAttempt.enrollment_id == enrollment_id).order_by(QuizAttempt.started_at.desc())
        )
        return list(result.scalars().all())

    async def get_option(self, option_id: uuid.UUID) -> QuizOption | None:
        return (await self._db.execute(select(QuizOption).where(QuizOption.id == option_id))).scalar_one_or_none()

    async def get_answer_for_question(self, attempt_id: uuid.UUID, question_id: uuid.UUID) -> QuizAnswer | None:
        return (await self._db.execute(
            select(QuizAnswer).where(QuizAnswer.attempt_id == attempt_id, QuizAnswer.question_id == question_id)
        )).scalar_one_or_none()

    async def get_answers_for_attempt(self, attempt_id: uuid.UUID) -> list[QuizAnswer]:
        result = await self._db.execute(select(QuizAnswer).where(QuizAnswer.attempt_id == attempt_id))
        return list(result.scalars().all())
