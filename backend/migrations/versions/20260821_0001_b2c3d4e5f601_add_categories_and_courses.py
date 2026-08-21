"""add categories and courses

Revision ID: b2c3d4e5f601
Revises: a1b2c3d4e5f6
Create Date: 2026-08-21 00:01:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "b2c3d4e5f601"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE course_status AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED')")

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_categories_name"),
    )

    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("DRAFT", "PUBLISHED", "ARCHIVED", name="course_status", create_type=False),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT", name="fk_courses_owner"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL", name="fk_courses_category"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_courses_owner_id", "courses", ["owner_id"])
    op.create_index("idx_courses_category_id", "courses", ["category_id"])
    op.create_index("idx_courses_status", "courses", ["status"])
    op.create_index("idx_courses_owner_status", "courses", ["owner_id", "status"])


def downgrade() -> None:
    op.drop_index("idx_courses_owner_status", table_name="courses")
    op.drop_index("idx_courses_status", table_name="courses")
    op.drop_index("idx_courses_category_id", table_name="courses")
    op.drop_index("idx_courses_owner_id", table_name="courses")
    op.drop_table("courses")
    op.drop_table("categories")
    op.execute("DROP TYPE IF EXISTS course_status")
