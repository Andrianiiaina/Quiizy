import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StorageBackend(str, enum.Enum):
    LOCAL = "LOCAL"
    S3 = "S3"


class FileAsset(Base):
    __tablename__ = "file_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    original_filename: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(sa.BigInteger, nullable=False)
    storage_backend: Mapped[StorageBackend] = mapped_column(
        sa.Enum(StorageBackend, name="storage_backend", create_type=False),
        nullable=False,
        server_default="LOCAL",
    )
    storage_path: Mapped[str] = mapped_column(sa.Text, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
    )
