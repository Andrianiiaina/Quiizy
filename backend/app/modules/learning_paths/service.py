import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.learning_paths.models import LearningPath, LPStatus
from app.modules.learning_paths.repository import LPRepository
from app.modules.learning_paths.schemas import ReorderCourseItem


class LPService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = LPRepository(db)

    async def create(self, *, created_by: uuid.UUID, title: str, description: str | None) -> LearningPath:
        lp = await self._repo.create(created_by=created_by, title=title, description=description)
        await self._db.commit()
        return await self._repo.get_by_id(lp.id)  # type: ignore[return-value]

    async def update(self, lp: LearningPath, data: dict) -> LearningPath:
        lp = await self._repo.update(lp, data)
        await self._db.commit()
        return lp

    async def delete(self, lp: LearningPath) -> None:
        await self._repo.delete(lp)
        await self._db.commit()

    async def set_status(self, lp: LearningPath, new_status: LPStatus) -> LearningPath:
        if new_status == LPStatus.PUBLISHED and lp.status != LPStatus.DRAFT:
            raise AppException(code="INVALID_STATUS_TRANSITION", message=f"Cannot publish LP with status '{lp.status.value}'.", status_code=409)
        if new_status == LPStatus.ARCHIVED and lp.status != LPStatus.PUBLISHED:
            raise AppException(code="INVALID_STATUS_TRANSITION", message=f"Cannot archive LP with status '{lp.status.value}'.", status_code=409)
        lp.status = new_status
        lp.updated_at = datetime.now(timezone.utc)
        await self._db.commit()
        return lp

    async def add_course(self, lp: LearningPath, course_id: uuid.UUID) -> None:
        if await self._repo.has_course(lp.id, course_id):
            raise AppException(code="COURSE_ALREADY_IN_LP", message="This course is already in the learning path.", status_code=409)
        await self._repo.add_course(lp.id, course_id)
        await self._db.commit()

    async def remove_course(self, lp: LearningPath, course_id: uuid.UUID) -> None:
        await self._repo.remove_course(lp.id, course_id)
        await self._db.commit()

    async def reorder_courses(self, lp: LearningPath, items: list[ReorderCourseItem]) -> None:
        from sqlalchemy import update
        from app.modules.learning_paths.models import LearningPathCourse
        for item in items:
            await self._db.execute(
                update(LearningPathCourse)
                .where(LearningPathCourse.learning_path_id == lp.id, LearningPathCourse.course_id == item.course_id)
                .values(position=item.position)
            )
        await self._db.commit()
