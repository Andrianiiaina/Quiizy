import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.assignments.models import (
    Assignment, AssignmentTargetType, Enrollment,
)
from app.modules.assignments.repository import AssignmentRepository
from app.modules.courses.repository import CourseRepository
from app.modules.learning_paths.repository import LPRepository


class AssignmentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = AssignmentRepository(db)

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        assigned_by: uuid.UUID,
        target_type: AssignmentTargetType,
        target_id: uuid.UUID,
        starts_at,
        due_date,
    ) -> Assignment:
        # Determine courses to enroll in
        if target_type == AssignmentTargetType.COURSE:
            course = await CourseRepository(self._db).get_by_id_or_none(target_id)
            if not course:
                raise AppException(code="COURSE_NOT_FOUND", message="Course not found.", status_code=404)
            course_ids = [target_id]
            lp_id = None
        else:
            lp_courses = await LPRepository(self._db).get_courses(target_id)
            if not lp_courses:
                raise AppException(code="LP_HAS_NO_COURSES", message="This learning path has no courses.", status_code=422)
            course_ids = [lpc.course_id for lpc in lp_courses]
            lp_id = target_id

        assignment = await self._repo.create(
            user_id=user_id,
            assigned_by=assigned_by,
            target_type=target_type,
            target_id=target_id,
            starts_at=starts_at,
            due_date=due_date,
        )

        for course_id in course_ids:
            await self._repo.create_enrollment(
                user_id=user_id,
                assignment_id=assignment.id,
                course_id=course_id,
                learning_path_id=lp_id,
                due_date=due_date,
            )

        await self._db.commit()
        return assignment

    async def cancel(self, assignment: Assignment) -> Assignment:
        from app.modules.assignments.models import AssignmentStatus, EnrollmentStatus
        from sqlalchemy import update, select
        from app.modules.assignments.models import Enrollment
        assignment.status = AssignmentStatus.CANCELLED
        await self._db.execute(
            update(Enrollment)
            .where(Enrollment.assignment_id == assignment.id)
            .values(status=EnrollmentStatus.CANCELLED)
        )
        await self._db.commit()
        return assignment
