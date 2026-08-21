"""add file_assets and course_contents

Revision ID: c3d4e5f60234
Revises: b2c3d4e5f601
Create Date: 2026-08-21 00:02:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "c3d4e5f60234"
down_revision: Union[str, None] = "b2c3d4e5f601"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE storage_backend AS ENUM ('LOCAL', 'S3')")
    op.execute("CREATE TYPE content_type AS ENUM ('TEXT', 'PDF', 'CSV', 'AUDIO', 'WEB_LINK')")

    op.create_table(
        "file_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column(
            "storage_backend",
            postgresql.ENUM("LOCAL", "S3", name="storage_backend", create_type=False),
            nullable=False,
            server_default="LOCAL",
        ),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT", name="fk_file_assets_user"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename", name="uq_file_assets_stored_filename"),
    )
    op.create_index("idx_file_assets_uploaded_by", "file_assets", ["uploaded_by"])

    op.add_column("courses", sa.Column("cover_image_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_courses_cover_image", "courses", "file_assets",
        ["cover_image_id"], ["id"], ondelete="SET NULL",
    )

    op.create_table(
        "course_contents",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM("TEXT", "PDF", "CSV", "AUDIO", "WEB_LINK", name="content_type", create_type=False),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("text_content", sa.Text, nullable=True),
        sa.Column("file_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("external_url", sa.Text, nullable=True),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE", name="fk_course_contents_course"),
        sa.ForeignKeyConstraint(["file_asset_id"], ["file_assets.id"], ondelete="SET NULL", name="fk_course_contents_file"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_course_contents_course_position", "course_contents", ["course_id", "position"])
    op.create_index("idx_course_contents_file_asset", "course_contents", ["file_asset_id"])


def downgrade() -> None:
    op.drop_index("idx_course_contents_file_asset", table_name="course_contents")
    op.drop_index("idx_course_contents_course_position", table_name="course_contents")
    op.drop_table("course_contents")
    op.drop_constraint("fk_courses_cover_image", "courses", type_="foreignkey")
    op.drop_column("courses", "cover_image_id")
    op.drop_index("idx_file_assets_uploaded_by", table_name="file_assets")
    op.drop_table("file_assets")
    op.execute("DROP TYPE IF EXISTS content_type")
    op.execute("DROP TYPE IF EXISTS storage_backend")
