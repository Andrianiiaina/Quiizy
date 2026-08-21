"""add assignments enrollments progress

Revision ID: e5f601234567
Revises: d4e5f6012345
Create Date: 2026-08-21 00:04:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "e5f601234567"
down_revision: Union[str, None] = "d4e5f6012345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE assignment_target_type AS ENUM ('COURSE', 'LEARNING_PATH')")
    op.execute("CREATE TYPE assignment_status AS ENUM ('PENDING', 'ACTIVE', 'COMPLETED', 'EXPIRED', 'CANCELLED')")
    op.execute("CREATE TYPE enrollment_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE', 'CANCELLED')")
    op.execute("CREATE TYPE progress_status AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED')")

    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_type", postgresql.ENUM("COURSE", "LEARNING_PATH", name="assignment_target_type", create_type=False), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", postgresql.ENUM("PENDING", "ACTIVE", "COMPLETED", "EXPIRED", "CANCELLED", name="assignment_status", create_type=False), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT", name="fk_assignments_user"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="RESTRICT", name="fk_assignments_assigner"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_assignments_user_id", "assignments", ["user_id"])
    op.create_index("idx_assignments_target", "assignments", ["target_type", "target_id"])

    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("learning_path_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", postgresql.ENUM("NOT_STARTED", "IN_PROGRESS", "COMPLETED", "OVERDUE", "CANCELLED", name="enrollment_status", create_type=False), nullable=False, server_default="NOT_STARTED"),
        sa.Column("progress_percent", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT", name="fk_enrollments_user"),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="RESTRICT", name="fk_enrollments_assignment"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="RESTRICT", name="fk_enrollments_course"),
        sa.ForeignKeyConstraint(["learning_path_id"], ["learning_paths.id"], ondelete="SET NULL", name="fk_enrollments_lp"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assignment_id", "course_id", name="uq_enrollments_assignment_course"),
    )
    op.create_index("idx_enrollments_user_id", "enrollments", ["user_id"])
    op.create_index("idx_enrollments_course_id", "enrollments", ["course_id"])
    op.create_index("idx_enrollments_user_course", "enrollments", ["user_id", "course_id"])

    op.create_table(
        "content_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", postgresql.ENUM("NOT_STARTED", "IN_PROGRESS", "COMPLETED", name="progress_status", create_type=False), nullable=False, server_default="NOT_STARTED"),
        sa.Column("progress_percent", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("last_position", sa.Text, nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"], ondelete="CASCADE", name="fk_cp_enrollment"),
        sa.ForeignKeyConstraint(["content_id"], ["course_contents.id"], ondelete="CASCADE", name="fk_cp_content"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("enrollment_id", "content_id", name="uq_content_progress"),
    )
    op.create_index("idx_content_progress_enrollment", "content_progress", ["enrollment_id"])


def downgrade() -> None:
    op.drop_index("idx_content_progress_enrollment", table_name="content_progress")
    op.drop_table("content_progress")
    op.drop_index("idx_enrollments_user_course", table_name="enrollments")
    op.drop_index("idx_enrollments_course_id", table_name="enrollments")
    op.drop_index("idx_enrollments_user_id", table_name="enrollments")
    op.drop_table("enrollments")
    op.drop_index("idx_assignments_target", table_name="assignments")
    op.drop_index("idx_assignments_user_id", table_name="assignments")
    op.drop_table("assignments")
    op.execute("DROP TYPE IF EXISTS progress_status")
    op.execute("DROP TYPE IF EXISTS enrollment_status")
    op.execute("DROP TYPE IF EXISTS assignment_status")
    op.execute("DROP TYPE IF EXISTS assignment_target_type")
