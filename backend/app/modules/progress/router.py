import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException, NotFoundError
from app.modules.auth.dependencies import get_current_user
from app.modules.assignments.repository import EnrollmentRepository
from app.modules.contents.repository import ContentRepository
from app.modules.progress.repository import ProgressRepository
from app.modules.progress.schemas import ContentProgressResponse, UpdateProgressRequest
from app.modules.progress.service import ProgressService
from app.modules.users.models import User, UserRole

router = APIRouter(tags=["progress"])


@router.get("/enrollments/{enrollment_id}/progress", response_model=list[ContentProgressResponse])
async def get_enrollment_progress(enrollment_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[ContentProgressResponse]:
    e = await EnrollmentRepository(db).get_by_id(enrollment_id)
    if not e:
        raise NotFoundError("Enrollment", str(enrollment_id))
    if e.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise NotFoundError("Enrollment", str(enrollment_id))
    items = await ProgressRepository(db).get_for_enrollment(enrollment_id)
    return [ContentProgressResponse.model_validate(cp) for cp in items]


@router.post("/enrollments/{enrollment_id}/contents/{content_id}/progress", response_model=ContentProgressResponse)
async def update_content_progress(
    enrollment_id: uuid.UUID,
    content_id: uuid.UUID,
    body: UpdateProgressRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContentProgressResponse:
    e = await EnrollmentRepository(db).get_by_id(enrollment_id)
    if not e:
        raise NotFoundError("Enrollment", str(enrollment_id))
    if e.user_id != current_user.id:
        raise AppException(code="ACCESS_DENIED", message="You can only update your own progress.", status_code=403)
    cp = await ProgressService(db).update_content_progress(
        enrollment_id=enrollment_id,
        content_id=content_id,
        status=body.status,
        progress_percent=body.progress_percent,
        last_position=body.last_position,
    )
    return ContentProgressResponse.model_validate(cp)
