import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException, NotFoundError
from app.modules.auth.dependencies import get_current_user
from app.modules.courses.models import Course, CourseStatus
from app.modules.courses.repository import CourseRepository
from app.modules.users.models import User, UserRole


async def get_course_or_404(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Course:
    course = await CourseRepository(db).get_by_id_or_none(course_id)
    if not course:
        raise NotFoundError("Course", str(course_id))
    return course


async def get_visible_course_or_404(
    course: Course = Depends(get_course_or_404),
    current_user: User = Depends(get_current_user),
) -> Course:
    # DRAFT/ARCHIVED → 404 for non-owners (don't reveal existence)
    if (
        course.status != CourseStatus.PUBLISHED
        and course.owner_id != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise NotFoundError("Course", str(course.id))
    return course


async def require_course_owner_or_admin(
    course: Course = Depends(get_visible_course_or_404),
    current_user: User = Depends(get_current_user),
) -> Course:
    if course.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise AppException(
            code="COURSE_ACCESS_DENIED",
            message="You do not have permission to modify this course.",
            status_code=403,
        )
    return course
