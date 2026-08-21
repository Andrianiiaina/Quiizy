import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ProgressStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ContentProgress(Base):
    __tablename__ = "content_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()"))
    enrollment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), sa.ForeignKey("course_contents.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[ProgressStatus] = mapped_column(sa.Enum(ProgressStatus, name="progress_status", create_type=False), nullable=False, server_default="NOT_STARTED")
    progress_percent: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False, server_default="0")
    last_position: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
