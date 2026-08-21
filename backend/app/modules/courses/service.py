import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.categories.repository import CategoryRepository
from app.modules.courses.models import Course, CourseStatus
from app.modules.courses.repository import CourseRepository


class CourseService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = CourseRepository(db)

    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        title: str,
        description: str | None,
        category_id: uuid.UUID | None,
    ) -> Course:
        await self._validate_category(category_id)
        raw = await self._repo.create(
            owner_id=owner_id,
            title=title,
            description=description,
            category_id=category_id,
        )
        await self._db.commit()
        return await self._repo.get_by_id_or_none(raw.id)  # type: ignore[return-value]

    async def update(self, course: Course, *, data: dict) -> Course:
        if "category_id" in data:
            await self._validate_category(data["category_id"])
        for key, value in data.items():
            if key == "title" and value is None:
                continue  # don't clear a required field
            setattr(course, key, value)
        course.updated_at = datetime.now(timezone.utc)
        await self._db.commit()
        return await self._repo.get_by_id_or_none(course.id)  # type: ignore[return-value]

    async def delete(self, course: Course) -> None:
        await self._repo.delete(course)
        await self._db.commit()

    async def publish(self, course: Course) -> Course:
        if course.status != CourseStatus.DRAFT:
            raise AppException(
                code="INVALID_STATUS_TRANSITION",
                message=f"Cannot publish a course with status '{course.status.value}'.",
                status_code=409,
            )
        course.status = CourseStatus.PUBLISHED
        course.updated_at = datetime.now(timezone.utc)
        await self._db.commit()
        return await self._repo.get_by_id_or_none(course.id)  # type: ignore[return-value]

    async def archive(self, course: Course) -> Course:
        if course.status != CourseStatus.PUBLISHED:
            raise AppException(
                code="INVALID_STATUS_TRANSITION",
                message=f"Cannot archive a course with status '{course.status.value}'.",
                status_code=409,
            )
        course.status = CourseStatus.ARCHIVED
        course.updated_at = datetime.now(timezone.utc)
        await self._db.commit()
        return await self._repo.get_by_id_or_none(course.id)  # type: ignore[return-value]

    async def _validate_category(self, category_id: uuid.UUID | None) -> None:
        if category_id is None:
            return
        if not await CategoryRepository(self._db).get_by_id(category_id):
            raise AppException(
                code="CATEGORY_NOT_FOUND",
                message=f"Category '{category_id}' not found.",
                status_code=404,
            )
