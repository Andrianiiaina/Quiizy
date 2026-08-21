import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.assignments.models import Assignment, Enrollment, EnrollmentStatus


class AssignmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all(self) -> list[Assignment]:
        result = await self._db.execute(select(Assignment).order_by(Assignment.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, assignment_id: uuid.UUID) -> Assignment | None:
        return (await self._db.execute(select(Assignment).where(Assignment.id == assignment_id))).scalar_one_or_none()

    async def create(self, **kwargs) -> Assignment:
        a = Assignment(**kwargs)
        self._db.add(a)
        await self._db.flush()
        await self._db.refresh(a)
        return a

    async def create_enrollment(self, **kwargs) -> Enrollment:
        e = Enrollment(**kwargs)
        self._db.add(e)
        await self._db.flush()
        return e


class EnrollmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_for_user(self, user_id: uuid.UUID) -> list[Enrollment]:
        result = await self._db.execute(
            select(Enrollment).where(Enrollment.user_id == user_id).order_by(Enrollment.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[Enrollment]:
        result = await self._db.execute(select(Enrollment).order_by(Enrollment.created_at.desc()))
        return list(result.scalars().all())

    async def get_by_id(self, enrollment_id: uuid.UUID) -> Enrollment | None:
        return (await self._db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))).scalar_one_or_none()

    async def get_by_user_and_course(self, user_id: uuid.UUID, course_id: uuid.UUID) -> Enrollment | None:
        result = await self._db.execute(
            select(Enrollment).where(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id,
                Enrollment.status.notin_([EnrollmentStatus.CANCELLED]),
            )
        )
        return result.scalar_one_or_none()
