import uuid
from pathlib import Path

import filetype
import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.modules.courses.models import Course, CourseStatus
from app.modules.files.models import FileAsset
from app.modules.files.repository import FileAssetRepository
from app.modules.files.storage import FileStorage
from app.modules.users.models import User, UserRole

ALLOWED_EXTENSIONS = frozenset({
    ".pdf", ".csv",
    ".mp3", ".wav", ".ogg", ".m4a", ".mp4",
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
})

DANGEROUS_EXTENSIONS = frozenset({
    ".exe", ".sh", ".bash", ".bat", ".cmd",
    ".php", ".py", ".js", ".html", ".vbs", ".ps1",
})

ALLOWED_MIMES = frozenset({
    "application/pdf",
    "text/csv", "text/plain",
    "audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/webm", "audio/aac",
    "image/jpeg", "image/png", "image/webp", "image/gif",
})


class FileService:
    def __init__(self, db: AsyncSession, storage: FileStorage) -> None:
        self._db = db
        self._repo = FileAssetRepository(db)
        self._storage = storage

    async def upload(
        self,
        data: bytes,
        original_filename: str,
        uploaded_by: uuid.UUID,
    ) -> FileAsset:
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(data) > max_bytes:
            raise AppException(
                code="FILE_TOO_LARGE",
                message=f"File size exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
                status_code=413,
            )

        ext = Path(original_filename).suffix.lower()
        if ext in DANGEROUS_EXTENSIONS or ext not in ALLOWED_EXTENSIONS:
            raise AppException(
                code="UNSUPPORTED_FILE_TYPE",
                message=f"File extension '{ext}' is not allowed.",
                status_code=422,
            )

        kind = filetype.guess(data)
        mime_type = kind.mime if kind else "application/octet-stream"
        if mime_type not in ALLOWED_MIMES:
            raise AppException(
                code="UNSUPPORTED_MIME_TYPE",
                message=f"MIME type '{mime_type}' is not allowed.",
                status_code=422,
            )

        stored_filename = f"{uuid.uuid4()}{ext}"
        storage_path = await self._storage.save(data, stored_filename)

        fa = await self._repo.create(
            original_filename=original_filename,
            stored_filename=stored_filename,
            mime_type=mime_type,
            size_bytes=len(data),
            storage_path=storage_path,
            uploaded_by=uploaded_by,
            storage_backend=settings.STORAGE_BACKEND,
        )
        await self._db.commit()
        return fa

    async def can_access(self, fa: FileAsset, current_user: User) -> bool:
        if current_user.role == UserRole.ADMIN:
            return True
        if fa.uploaded_by == current_user.id:
            return True
        # Allow if the file is referenced by a course content the user can see
        from app.modules.contents.models import CourseContent  # lazy import avoids circularity
        result = await self._db.execute(
            select(CourseContent)
            .join(Course, CourseContent.course_id == Course.id)
            .where(
                CourseContent.file_asset_id == fa.id,
                sa.or_(
                    Course.status == CourseStatus.PUBLISHED,
                    Course.owner_id == current_user.id,
                ),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def delete_asset(self, fa: FileAsset, current_user: User) -> None:
        if fa.uploaded_by != current_user.id and current_user.role != UserRole.ADMIN:
            raise AppException(
                code="FILE_ACCESS_DENIED",
                message="You do not have permission to delete this file.",
                status_code=403,
            )
        await self._storage.delete(fa.storage_path)
        await self._repo.delete(fa)
        await self._db.commit()
