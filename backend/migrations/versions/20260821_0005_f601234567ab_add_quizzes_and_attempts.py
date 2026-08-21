"""add quizzes and attempts

Revision ID: f601234567ab
Revises: e5f601234567
Create Date: 2026-08-21 00:05:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "f601234567ab"
down_revision: Union[str, None] = "e5f601234567"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE quiz_status AS ENUM ('DRAFT', 'ACTIVE', 'ARCHIVED')")
    op.execute("CREATE TYPE quiz_difficulty AS ENUM ('EASY', 'MEDIUM', 'HARD')")
    op.execute("CREATE TYPE job_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')")

    op.create_table(
        "quizzes",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", postgresql.ENUM("DRAFT", "ACTIVE", "ARCHIVED", name="quiz_status", create_type=False), nullable=False, server_default="DRAFT"),
        sa.Column("difficulty", postgresql.ENUM("EASY", "MEDIUM", "HARD", name="quiz_difficulty", create_type=False), nullable=False, server_default="MEDIUM"),
        sa.Column("question_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE", name="fk_quizzes_course"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("course_id", "version", name="uq_quiz_course_version"),
    )
    op.create_index("idx_quizzes_course_id", "quizzes", ["course_id"])

    op.create_table(
        "quiz_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("explanation", sa.Text, nullable=False),
        sa.Column("source_content_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_reference", sa.Text, nullable=True),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE", name="fk_qq_quiz"),
        sa.ForeignKeyConstraint(["source_content_id"], ["course_contents.id"], ondelete="SET NULL", name="fk_qq_content"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_quiz_questions_quiz_id", "quiz_questions", ["quiz_id"])

    op.create_table(
        "quiz_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("is_correct", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["question_id"], ["quiz_questions.id"], ondelete="CASCADE", name="fk_qo_question"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_quiz_options_question_id", "quiz_options", ["question_id"])
    # Enforce at most one correct answer per question
    op.create_index("uq_one_correct_per_question", "quiz_options", ["question_id"], unique=True, postgresql_where=sa.text("is_correct = true"))

    op.create_table(
        "quiz_generation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", postgresql.ENUM("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="job_status", create_type=False), nullable=False, server_default="PENDING"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE", name="fk_job_course"),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"], ondelete="RESTRICT", name="fk_job_user"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_quiz_gen_jobs_course", "quiz_generation_jobs", ["course_id"])

    op.create_table(
        "quiz_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.SmallInteger, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="RESTRICT", name="fk_attempt_quiz"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT", name="fk_attempt_user"),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"], ondelete="RESTRICT", name="fk_attempt_enrollment"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_quiz_attempts_enrollment", "quiz_attempts", ["enrollment_id"])
    op.create_index("idx_quiz_attempts_user", "quiz_attempts", ["user_id"])

    op.create_table(
        "quiz_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("selected_option_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_correct", sa.Boolean, nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["quiz_attempts.id"], ondelete="CASCADE", name="fk_answer_attempt"),
        sa.ForeignKeyConstraint(["question_id"], ["quiz_questions.id"], ondelete="RESTRICT", name="fk_answer_question"),
        sa.ForeignKeyConstraint(["selected_option_id"], ["quiz_options.id"], ondelete="RESTRICT", name="fk_answer_option"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "question_id", name="uq_answer_per_question"),
    )
    op.create_index("idx_quiz_answers_attempt", "quiz_answers", ["attempt_id"])


def downgrade() -> None:
    op.drop_index("idx_quiz_answers_attempt", table_name="quiz_answers")
    op.drop_table("quiz_answers")
    op.drop_index("idx_quiz_attempts_user", table_name="quiz_attempts")
    op.drop_index("idx_quiz_attempts_enrollment", table_name="quiz_attempts")
    op.drop_table("quiz_attempts")
    op.drop_index("idx_quiz_gen_jobs_course", table_name="quiz_generation_jobs")
    op.drop_table("quiz_generation_jobs")
    op.drop_index("uq_one_correct_per_question", table_name="quiz_options")
    op.drop_index("idx_quiz_options_question_id", table_name="quiz_options")
    op.drop_table("quiz_options")
    op.drop_index("idx_quiz_questions_quiz_id", table_name="quiz_questions")
    op.drop_table("quiz_questions")
    op.drop_index("idx_quizzes_course_id", table_name="quizzes")
    op.drop_table("quizzes")
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS quiz_difficulty")
    op.execute("DROP TYPE IF EXISTS quiz_status")
