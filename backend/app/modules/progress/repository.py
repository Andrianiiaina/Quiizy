import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.progress.models import ContentProgress, ProgressStatus
from app.modules.assignments.models import Enrollment, EnrollmentStatus


class ProgressRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_for_enrollment(self, enrollment_id: uuid.UUID) -> list[ContentProgress]:
        result = await self._db.execute(
            select(ContentProgress).where(ContentProgress.enrollment_id == enrollment_id)
        )
        return list(result.scalars().all())

    async def get_by_enrollment_content(self, enrollment_id: uuid.UUID, content_id: uuid.UUID) -> ContentProgress | None:
        return (await self._db.execute(
            select(ContentProgress).where(
                ContentProgress.enrollment_id == enrollment_id,
                ContentProgress.content_id == content_id,
            )
        )).scalar_one_or_none()

    async def upsert(self, enrollment_id: uuid.UUID, content_id: uuid.UUID, status: ProgressStatus, progress_percent: int, last_position: str | None) -> ContentProgress:
        existing = await self.get_by_enrollment_content(enrollment_id, content_id)
        now = datetime.now(timezone.utc)
        if existing:
            existing.status = status
            existing.progress_percent = progress_percent
            if last_position is not None:
                existing.last_position = last_position
            if status == ProgressStatus.COMPLETED and not existing.completed_at:
                existing.completed_at = now
            await self._db.flush()
            return existing
        cp = ContentProgress(enrollment_id=enrollment_id, content_id=content_id, status=status, progress_percent=progress_percent, last_position=last_position, completed_at=now if status == ProgressStatus.COMPLETED else None)
        self._db.add(cp)
        await self._db.flush()
        return cp

    async def recalculate_enrollment(self, enrollment_id: uuid.UUID, total_contents: int) -> None:
        from app.modules.contents.models import CourseContent  # avoid circular
        completed = (await self._db.execute(
            select(sa.func.count()).select_from(ContentProgress).where(
                ContentProgress.enrollment_id == enrollment_id,
                ContentProgress.status == ProgressStatus.COMPLETED,
            )
        )).scalar_one()

        enrollment = (await self._db.execute(select(Enrollment).where(Enrollment.id == enrollment_id))).scalar_one_or_none()
        if not enrollment:
            return

        percent = int(completed / total_contents * 100) if total_contents > 0 else 0
        enrollment.progress_percent = percent
        now = datetime.now(timezone.utc)
        if percent == 100:
            enrollment.status = EnrollmentStatus.COMPLETED
            enrollment.completed_at = now
        elif percent > 0 and enrollment.status == EnrollmentStatus.NOT_STARTED:
            enrollment.status = EnrollmentStatus.IN_PROGRESS
            enrollment.started_at = enrollment.started_at or now
        await self._db.flush()
