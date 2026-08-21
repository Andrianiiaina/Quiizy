"""add learning paths

Revision ID: d4e5f6012345
Revises: c3d4e5f60234
Create Date: 2026-08-21 00:03:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "d4e5f6012345"
down_revision: Union[str, None] = "c3d4e5f60234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE lp_status AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED')")

    op.create_table(
        "learning_paths",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("cover_image_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", postgresql.ENUM("DRAFT", "PUBLISHED", "ARCHIVED", name="lp_status", create_type=False), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT", name="fk_lp_creator"),
        sa.ForeignKeyConstraint(["cover_image_id"], ["file_assets.id"], ondelete="SET NULL", name="fk_lp_cover"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_learning_paths_created_by", "learning_paths", ["created_by"])

    op.create_table(
        "learning_path_courses",
        sa.Column("learning_path_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["learning_path_id"], ["learning_paths.id"], ondelete="CASCADE", name="fk_lpc_lp"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE", name="fk_lpc_course"),
        sa.PrimaryKeyConstraint("learning_path_id", "course_id"),
    )
    op.create_index("idx_lpc_course_id", "learning_path_courses", ["course_id"])


def downgrade() -> None:
    op.drop_index("idx_lpc_course_id", table_name="learning_path_courses")
    op.drop_table("learning_path_courses")
    op.drop_index("idx_learning_paths_created_by", table_name="learning_paths")
    op.drop_table("learning_paths")
    op.execute("DROP TYPE IF EXISTS lp_status")
