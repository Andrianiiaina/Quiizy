import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuizStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class QuizDifficulty(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default="1")
    status: Mapped[QuizStatus] = mapped_column(sa.Enum(QuizStatus, name="quiz_status", create_type=False), nullable=False, server_default="DRAFT")
    difficulty: Mapped[QuizDifficulty] = mapped_column(sa.Enum(QuizDifficulty, name="quiz_difficulty", create_type=False), nullable=False, server_default="MEDIUM")
    question_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default="0")
    generated_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    questions: Mapped[list["QuizQuestion"]] = relationship("QuizQuestion", lazy="raise", order_by="QuizQuestion.position")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(sa.Text, nullable=False)
    explanation: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source_content_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("course_contents.id", ondelete="SET NULL"), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    position: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

    options: Mapped[list["QuizOption"]] = relationship("QuizOption", lazy="raise", order_by="QuizOption.position")


class QuizOption(Base):
    __tablename__ = "quiz_options"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.text("false"))
    position: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)


class QuizGenerationJob(Base):
    __tablename__ = "quiz_generation_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[JobStatus] = mapped_column(sa.Enum(JobStatus, name="job_status", create_type=False), nullable=False, server_default="PENDING")
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"))


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("quizzes.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("enrollments.id", ondelete="RESTRICT"), nullable=False, index=True)
    score: Mapped[int | None] = mapped_column(sa.SmallInteger, nullable=True)
    started_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()"))
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("quiz_questions.id", ondelete="RESTRICT"), nullable=False)
    selected_option_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("quiz_options.id", ondelete="RESTRICT"), nullable=False)
    is_correct: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
