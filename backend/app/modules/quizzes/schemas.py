import uuid
from datetime import datetime
from pydantic import BaseModel
from app.modules.quizzes.models import QuizStatus, QuizDifficulty, JobStatus


class QuizOptionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    text: str
    position: int


class QuizOptionWithAnswerResponse(QuizOptionResponse):
    is_correct: bool


class QuizQuestionResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    question: str
    position: int
    options: list[QuizOptionResponse] = []


class QuizQuestionResultResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    question: str
    explanation: str
    position: int
    options: list[QuizOptionWithAnswerResponse] = []


class QuizResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    course_id: uuid.UUID
    version: int
    status: QuizStatus
    difficulty: QuizDifficulty
    question_count: int
    generated_at: datetime | None


class QuizDetailResponse(QuizResponse):
    questions: list[QuizQuestionResponse] = []


class JobResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    course_id: uuid.UUID
    status: JobStatus
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime


class StartAttemptResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    quiz_id: uuid.UUID
    enrollment_id: uuid.UUID
    started_at: datetime
    completed_at: datetime | None
    score: int | None
    questions: list[QuizQuestionResponse] = []


class AnswerRequest(BaseModel):
    question_id: uuid.UUID
    selected_option_id: uuid.UUID


class AnswerResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    question_id: uuid.UUID
    selected_option_id: uuid.UUID
    is_correct: bool


class AttemptResultResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    quiz_id: uuid.UUID
    score: int | None
    started_at: datetime
    completed_at: datetime | None
    answers: list[AnswerResponse] = []
    questions: list[QuizQuestionResultResponse] = []
