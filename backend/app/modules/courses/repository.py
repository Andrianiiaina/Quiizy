import uuid

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.courses.models import Course, CourseStatus
from app.modules.users.models import User, UserRole


class CourseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all(
        self,
        *,
        current_user: User,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Course], int]:
        base = select(Course)
        count_base = select(sa.func.count()).select_from(Course)

        if current_user.role != UserRole.ADMIN:
            cond = sa.or_(
                Course.status == CourseStatus.PUBLISHED,
                Course.owner_id == current_user.id,
            )
            base = base.where(cond)
            count_base = count_base.where(cond)

        total = (await self._db.execute(count_base)).scalar_one()
        courses = list(
            (
                await self._db.execute(
                    base.options(selectinload(Course.category))
                    .order_by(Course.created_at.desc())
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                )
            ).scalars().all()
        )
        return courses, total

    async def get_by_id_or_none(self, course_id: uuid.UUID) -> Course | None:
        result = await self._db.execute(
            select(Course)
            .options(selectinload(Course.category))
            .where(Course.id == course_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        title: str,
        description: str | None,
        category_id: uuid.UUID | None,
    ) -> Course:
        course = Course(
            owner_id=owner_id,
            title=title,
            description=description,
            category_id=category_id,
        )
        self._db.add(course)
        await self._db.flush()
        return course

    async def delete(self, course: Course) -> None:
        await self._db.delete(course)
        await self._db.flush()
