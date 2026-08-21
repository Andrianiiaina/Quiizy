import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.assignments.models import Enrollment, EnrollmentStatus
from app.modules.assignments.repository import EnrollmentRepository
from app.modules.quizzes.models import (
    Quiz, QuizAnswer, QuizAttempt, QuizGenerationJob,
    QuizOption, QuizQuestion, QuizStatus, JobStatus,
)
from app.modules.quizzes.repository import QuizRepository


class QuizService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = QuizRepository(db)

    async def start_attempt(self, quiz_id: uuid.UUID, user_id: uuid.UUID, enrollment_id: uuid.UUID) -> QuizAttempt:
        open_attempt = await self._repo.get_open_attempt(user_id, quiz_id)
        if open_attempt:
            return open_attempt  # resume existing attempt

        enrollment = await EnrollmentRepository(self._db).get_by_id(enrollment_id)
        if not enrollment or enrollment.user_id != user_id:
            raise AppException(code="ENROLLMENT_NOT_FOUND", message="Enrollment not found.", status_code=404)

        attempt = QuizAttempt(quiz_id=quiz_id, user_id=user_id, enrollment_id=enrollment_id)
        self._db.add(attempt)
        await self._db.flush()
        await self._db.refresh(attempt)
        await self._db.commit()
        return attempt

    async def submit_answer(self, attempt_id: uuid.UUID, question_id: uuid.UUID, selected_option_id: uuid.UUID) -> QuizAnswer:
        attempt = await self._repo.get_attempt(attempt_id)
        if not attempt or attempt.completed_at:
            raise AppException(code="ATTEMPT_CLOSED", message="Attempt is already completed or not found.", status_code=409)

        existing = await self._repo.get_answer_for_question(attempt_id, question_id)
        if existing:
            raise AppException(code="ALREADY_ANSWERED", message="This question has already been answered.", status_code=409)

        option = await self._repo.get_option(selected_option_id)
        if not option or option.question_id != question_id:
            raise AppException(code="INVALID_OPTION", message="Option does not belong to this question.", status_code=422)

        answer = QuizAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            is_correct=option.is_correct,
        )
        self._db.add(answer)
        await self._db.flush()
        await self._db.refresh(answer)
        await self._db.commit()
        return answer

    async def complete_attempt(self, attempt_id: uuid.UUID, user_id: uuid.UUID) -> QuizAttempt:
        attempt = await self._repo.get_attempt(attempt_id)
        if not attempt or attempt.user_id != user_id:
            raise AppException(code="ATTEMPT_NOT_FOUND", message="Attempt not found.", status_code=404)
        if attempt.completed_at:
            raise AppException(code="ALREADY_COMPLETED", message="Attempt already completed.", status_code=409)

        answers = await self._repo.get_answers_for_attempt(attempt_id)
        quiz = await self._repo.get_by_id(attempt.quiz_id)
        total = quiz.question_count if quiz else len(answers)
        correct = sum(1 for a in answers if a.is_correct)
        attempt.score = int(correct / total * 100) if total > 0 else 0
        attempt.completed_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.commit()

        # Update enrollment status if score is sufficient
        enrollment = await EnrollmentRepository(self._db).get_by_id(attempt.enrollment_id)
        if enrollment and enrollment.status == EnrollmentStatus.IN_PROGRESS and attempt.score is not None and attempt.score >= 60:
            if enrollment.progress_percent >= 100:
                enrollment.status = EnrollmentStatus.COMPLETED
                enrollment.completed_at = enrollment.completed_at or datetime.now(timezone.utc)
                await self._db.commit()

        return attempt
