import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.contents.models import ContentType, CourseContent


class ContentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_course(self, course_id: uuid.UUID) -> list[CourseContent]:
        result = await self._db.execute(
            select(CourseContent)
            .options(selectinload(CourseContent.file_asset))
            .where(CourseContent.course_id == course_id)
            .order_by(CourseContent.position.asc(), CourseContent.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_id_or_none(self, content_id: uuid.UUID) -> CourseContent | None:
        result = await self._db.execute(
            select(CourseContent)
            .options(
                selectinload(CourseContent.file_asset),
                selectinload(CourseContent.course_rel),
            )
            .where(CourseContent.id == content_id)
        )
        return result.scalar_one_or_none()

    async def get_max_position(self, course_id: uuid.UUID) -> int:
        result = await self._db.execute(
            select(sa.func.coalesce(sa.func.max(CourseContent.position), -1))
            .where(CourseContent.course_id == course_id)
        )
        return result.scalar_one()

    async def create(
        self,
        *,
        course_id: uuid.UUID,
        content_type: ContentType,
        title: str,
        text_content: str | None,
        file_asset_id: uuid.UUID | None,
        external_url: str | None,
        position: int,
    ) -> CourseContent:
        content = CourseContent(
            course_id=course_id,
            type=content_type,
            title=title,
            text_content=text_content,
            file_asset_id=file_asset_id,
            external_url=external_url,
            position=position,
        )
        self._db.add(content)
        await self._db.flush()
        return content

    async def bulk_update_positions(self, positions: dict[uuid.UUID, int]) -> None:
        now = datetime.now(timezone.utc)
        for content_id, position in positions.items():
            await self._db.execute(
                sa.update(CourseContent)
                .where(CourseContent.id == content_id)
                .values(position=position, updated_at=now)
            )

    async def delete(self, content: CourseContent) -> None:
        await self._db.delete(content)
        await self._db.flush()
