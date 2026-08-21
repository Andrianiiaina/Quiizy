import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.assignments.models import Enrollment, EnrollmentStatus
from app.modules.assignments.repository import EnrollmentRepository
from app.modules.contents.repository import ContentRepository
from app.modules.progress.models import ProgressStatus
from app.modules.progress.repository import ProgressRepository


class ProgressService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def update_content_progress(
        self,
        *,
        enrollment_id: uuid.UUID,
        content_id: uuid.UUID,
        status: ProgressStatus,
        progress_percent: int,
        last_position: str | None,
    ):
        enrollment = await EnrollmentRepository(self._db).get_by_id(enrollment_id)
        if not enrollment:
            raise AppException(code="ENROLLMENT_NOT_FOUND", message="Enrollment not found.", status_code=404)

        if enrollment.status == EnrollmentStatus.CANCELLED:
            raise AppException(code="ENROLLMENT_CANCELLED", message="This enrollment has been cancelled.", status_code=409)

        if enrollment.status == EnrollmentStatus.NOT_STARTED and status != ProgressStatus.NOT_STARTED:
            enrollment.status = EnrollmentStatus.IN_PROGRESS
            enrollment.started_at = enrollment.started_at or datetime.now(timezone.utc)

        progress_repo = ProgressRepository(self._db)
        cp = await progress_repo.upsert(
            enrollment_id=enrollment_id,
            content_id=content_id,
            status=status,
            progress_percent=progress_percent,
            last_position=last_position,
        )

        total_contents = len(await ContentRepository(self._db).list_for_course(enrollment.course_id))
        await progress_repo.recalculate_enrollment(enrollment_id, total_contents)
        await self._db.commit()
        return cp
