import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.courses.models import Course
from app.modules.files.models import FileAsset


class ContentType(str, enum.Enum):
    TEXT = "TEXT"
    PDF = "PDF"
    CSV = "CSV"
    AUDIO = "AUDIO"
    WEB_LINK = "WEB_LINK"


class CourseContent(Base):
    __tablename__ = "course_contents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[ContentType] = mapped_column(
        sa.Enum(ContentType, name="content_type", create_type=False),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    text_content: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    file_asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("file_assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_url: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    position: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )

    file_asset: Mapped[FileAsset | None] = relationship("FileAsset", lazy="raise")
    course_rel: Mapped[Course] = relationship("Course", lazy="raise")
