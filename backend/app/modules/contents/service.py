import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.contents.models import ContentType, CourseContent
from app.modules.contents.repository import ContentRepository
from app.modules.contents.schemas import ReorderItem
from app.modules.files.repository import FileAssetRepository

FILE_TYPE_MIMES: dict[ContentType, frozenset[str]] = {
    ContentType.PDF:   frozenset({"application/pdf"}),
    ContentType.CSV:   frozenset({"text/csv", "text/plain", "application/csv"}),
    ContentType.AUDIO: frozenset({
        "audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4",
        "audio/webm", "audio/aac", "audio/x-wav",
    }),
}


def _validate_web_url(url: str) -> None:
    if not url.startswith("https://"):
        raise AppException(code="INVALID_URL", message="External URLs must use HTTPS.", status_code=422)
    if not re.match(r"^https://[^\s/$.?#][^\s]*$", url):
        raise AppException(code="INVALID_URL", message="Invalid URL format.", status_code=422)


class ContentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = ContentRepository(db)

    async def create(
        self,
        *,
        course_id: uuid.UUID,
        content_type: ContentType,
        title: str,
        text_content: str | None,
        file_asset_id: uuid.UUID | None,
        external_url: str | None,
    ) -> CourseContent:
        self._validate_payload(content_type, text_content, file_asset_id, external_url)
        if file_asset_id:
            await self._validate_file_mime(content_type, file_asset_id)

        position = await self._repo.get_max_position(course_id) + 1
        raw = await self._repo.create(
            course_id=course_id,
            content_type=content_type,
            title=title,
            text_content=text_content,
            file_asset_id=file_asset_id,
            external_url=external_url,
            position=position,
        )
        await self._db.commit()
        return await self._repo.get_by_id_or_none(raw.id)  # type: ignore[return-value]

    async def update(self, content: CourseContent, *, data: dict) -> CourseContent:
        for key, value in data.items():
            if key == "title" and value is None:
                continue
            setattr(content, key, value)
        content.updated_at = datetime.now(timezone.utc)
        await self._db.commit()
        return await self._repo.get_by_id_or_none(content.id)  # type: ignore[return-value]

    async def delete(self, content: CourseContent) -> None:
        await self._repo.delete(content)
        await self._db.commit()

    async def reorder(self, course_id: uuid.UUID, items: list[ReorderItem]) -> None:
        existing_ids = {c.id for c in await self._repo.list_for_course(course_id)}
        for item in items:
            if item.id not in existing_ids:
                raise AppException(
                    code="CONTENT_NOT_IN_COURSE",
                    message=f"Content '{item.id}' does not belong to this course.",
                    status_code=422,
                )
        await self._repo.bulk_update_positions({item.id: item.position for item in items})
        await self._db.commit()

    def _validate_payload(
        self,
        content_type: ContentType,
        text_content: str | None,
        file_asset_id: uuid.UUID | None,
        external_url: str | None,
    ) -> None:
        if content_type == ContentType.TEXT and not text_content:
            raise AppException(code="MISSING_FIELD", message="text_content is required for TEXT content.", status_code=422)
        if content_type in (ContentType.PDF, ContentType.CSV, ContentType.AUDIO) and not file_asset_id:
            raise AppException(code="MISSING_FIELD", message=f"file_asset_id is required for {content_type.value} content.", status_code=422)
        if content_type == ContentType.WEB_LINK:
            if not external_url:
                raise AppException(code="MISSING_FIELD", message="external_url is required for WEB_LINK content.", status_code=422)
            _validate_web_url(external_url)

    async def _validate_file_mime(self, content_type: ContentType, file_asset_id: uuid.UUID) -> None:
        fa = await FileAssetRepository(self._db).get_by_id(file_asset_id)
        if not fa:
            raise AppException(code="FILE_NOT_FOUND", message=f"FileAsset '{file_asset_id}' not found.", status_code=404)
        allowed = FILE_TYPE_MIMES.get(content_type)
        if allowed and fa.mime_type not in allowed:
            raise AppException(
                code="MIME_TYPE_MISMATCH",
                message=f"MIME type '{fa.mime_type}' is not compatible with {content_type.value} content.",
                status_code=422,
            )
