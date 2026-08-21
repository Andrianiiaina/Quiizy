import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException, NotFoundError
from app.modules.auth.dependencies import get_current_user
from app.modules.assignments.repository import EnrollmentRepository
from app.modules.courses.dependencies import require_course_owner_or_admin
from app.modules.courses.models import Course
from app.modules.quizzes.generation import run_generation_job, trigger_generation
from app.modules.quizzes.models import QuizStatus
from app.modules.quizzes.repository import QuizRepository
from app.modules.quizzes.schemas import (
    AnswerRequest, AnswerResponse, AttemptResultResponse,
    JobResponse, QuizDetailResponse, QuizResponse,
    StartAttemptResponse,
)
from app.modules.quizzes.service import QuizService
from app.modules.users.models import User, UserRole
from sqlalchemy.orm import selectinload
from sqlalchemy import select

router = APIRouter(tags=["quizzes"])


@router.post("/courses/{course_id}/quiz/generate", response_model=JobResponse, status_code=202)
async def generate_quiz(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    course: Course = Depends(require_course_owner_or_admin),
) -> JobResponse:
    job = await trigger_generation(course.id, course.owner_id, db)
    background_tasks.add_task(run_generation_job, job.id)
    return JobResponse.model_validate(job)


@router.get("/courses/{course_id}/quiz", response_model=QuizResponse)
async def get_active_quiz(course_id: uuid.UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> QuizResponse:
    quiz = await QuizRepository(db).get_active_for_course(course_id)
    if not quiz:
        raise NotFoundError("Quiz", str(course_id))
    return QuizResponse.model_validate(quiz)


@router.get("/quiz-generation-jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> JobResponse:
    job = await QuizRepository(db).get_job(job_id)
    if not job:
        raise NotFoundError("QuizGenerationJob", str(job_id))
    return JobResponse.model_validate(job)


@router.get("/quizzes/{quiz_id}", response_model=QuizDetailResponse)
async def get_quiz_detail(quiz_id: uuid.UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> QuizDetailResponse:
    from app.modules.quizzes.models import QuizQuestion, QuizOption
    quiz = await QuizRepository(db).get_with_questions(quiz_id)
    if not quiz:
        raise NotFoundError("Quiz", str(quiz_id))
    resp = QuizDetailResponse.model_validate(quiz)
    for q, qm in zip(resp.questions, quiz.questions):
        q.options = [type(q.options[0]).model_validate(o) if q.options else None for o in qm.options]  # type: ignore[misc]
    return resp


@router.post("/quizzes/{quiz_id}/attempts", response_model=StartAttemptResponse, status_code=201)
async def start_attempt(
    quiz_id: uuid.UUID,
    enrollment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StartAttemptResponse:
    svc = QuizService(db)
    attempt = await svc.start_attempt(quiz_id, current_user.id, enrollment_id)
    quiz = await QuizRepository(db).get_with_questions(quiz_id)

    from app.modules.quizzes.schemas import QuizOptionResponse, QuizQuestionResponse
    questions = []
    if quiz:
        for qm in quiz.questions:
            questions.append(QuizQuestionResponse(
                id=qm.id,
                question=qm.question,
                position=qm.position,
                options=[QuizOptionResponse(id=o.id, text=o.text, position=o.position) for o in qm.options],
            ))

    return StartAttemptResponse(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        enrollment_id=attempt.enrollment_id,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        score=attempt.score,
        questions=questions,
    )


@router.post("/quiz-attempts/{attempt_id}/answers", response_model=AnswerResponse)
async def submit_answer(attempt_id: uuid.UUID, body: AnswerRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> AnswerResponse:
    answer = await QuizService(db).submit_answer(attempt_id, body.question_id, body.selected_option_id)
    return AnswerResponse.model_validate(answer)


@router.post("/quiz-attempts/{attempt_id}/complete", response_model=AttemptResultResponse)
async def complete_attempt(attempt_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> AttemptResultResponse:
    attempt = await QuizService(db).complete_attempt(attempt_id, current_user.id)
    answers = await QuizRepository(db).get_answers_for_attempt(attempt_id)
    quiz = await QuizRepository(db).get_with_questions(attempt.quiz_id)

    from app.modules.quizzes.schemas import AnswerResponse as AR, QuizOptionWithAnswerResponse, QuizQuestionResultResponse
    answer_map = {a.question_id: a for a in answers}
    questions_result = []
    if quiz:
        for qm in quiz.questions:
            questions_result.append(QuizQuestionResultResponse(
                id=qm.id,
                question=qm.question,
                explanation=qm.explanation,
                position=qm.position,
                options=[QuizOptionWithAnswerResponse(id=o.id, text=o.text, is_correct=o.is_correct, position=o.position) for o in qm.options],
            ))

    return AttemptResultResponse(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        score=attempt.score,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        answers=[AR.model_validate(a) for a in answers],
        questions=questions_result,
    )


@router.get("/enrollments/{enrollment_id}/quiz-attempts", response_model=list[dict])
async def get_attempts_for_enrollment(enrollment_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict]:
    attempts = await QuizRepository(db).get_attempts_for_enrollment(enrollment_id)
    return [{"id": str(a.id), "quiz_id": str(a.quiz_id), "score": a.score, "completed_at": str(a.completed_at) if a.completed_at else None, "started_at": str(a.started_at)} for a in attempts]
