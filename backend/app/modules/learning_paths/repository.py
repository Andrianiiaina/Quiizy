import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning_paths.models import LearningPath, LearningPathCourse, LPStatus
from app.modules.users.models import UserRole


class LPRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all(self, *, current_user_id: uuid.UUID, is_admin: bool, page: int = 1, per_page: int = 20) -> tuple[list[LearningPath], int]:
        base = select(LearningPath)
        count_base = select(sa.func.count()).select_from(LearningPath)
        if not is_admin:
            cond = sa.or_(LearningPath.status == LPStatus.PUBLISHED, LearningPath.created_by == current_user_id)
            base = base.where(cond)
            count_base = count_base.where(cond)
        total = (await self._db.execute(count_base)).scalar_one()
        lps = list((await self._db.execute(base.order_by(LearningPath.created_at.desc()).offset((page-1)*per_page).limit(per_page))).scalars().all())
        return lps, total

    async def get_by_id(self, lp_id: uuid.UUID) -> LearningPath | None:
        return (await self._db.execute(select(LearningPath).where(LearningPath.id == lp_id))).scalar_one_or_none()

    async def get_courses(self, lp_id: uuid.UUID) -> list[LearningPathCourse]:
        result = await self._db.execute(
            select(LearningPathCourse).where(LearningPathCourse.learning_path_id == lp_id).order_by(LearningPathCourse.position)
        )
        return list(result.scalars().all())

    async def create(self, *, created_by: uuid.UUID, title: str, description: str | None) -> LearningPath:
        lp = LearningPath(created_by=created_by, title=title, description=description)
        self._db.add(lp)
        await self._db.flush()
        await self._db.refresh(lp)
        return lp

    async def update(self, lp: LearningPath, data: dict) -> LearningPath:
        for k, v in data.items():
            if k == "title" and v is None:
                continue
            setattr(lp, k, v)
        lp.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(lp)
        return lp

    async def delete(self, lp: LearningPath) -> None:
        await self._db.delete(lp)
        await self._db.flush()

    async def add_course(self, lp_id: uuid.UUID, course_id: uuid.UUID) -> LearningPathCourse:
        max_pos = (await self._db.execute(
            select(sa.func.coalesce(sa.func.max(LearningPathCourse.position), -1))
            .where(LearningPathCourse.learning_path_id == lp_id)
        )).scalar_one()
        lpc = LearningPathCourse(learning_path_id=lp_id, course_id=course_id, position=max_pos + 1)
        self._db.add(lpc)
        await self._db.flush()
        return lpc

    async def remove_course(self, lp_id: uuid.UUID, course_id: uuid.UUID) -> None:
        lpc = (await self._db.execute(
            select(LearningPathCourse).where(LearningPathCourse.learning_path_id == lp_id, LearningPathCourse.course_id == course_id)
        )).scalar_one_or_none()
        if lpc:
            await self._db.delete(lpc)
            await self._db.flush()

    async def has_course(self, lp_id: uuid.UUID, course_id: uuid.UUID) -> bool:
        result = await self._db.execute(
            select(LearningPathCourse).where(LearningPathCourse.learning_path_id == lp_id, LearningPathCourse.course_id == course_id)
        )
        return result.scalar_one_or_none() is not None
