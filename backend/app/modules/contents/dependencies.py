import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import AppException, NotFoundError
from app.modules.auth.dependencies import get_current_user
from app.modules.contents.models import CourseContent
from app.modules.users.models import User, UserRole


async def get_content_or_404(
    content_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CourseContent:
    result = await db.execute(
        select(CourseContent)
        .options(
            selectinload(CourseContent.file_asset),
            selectinload(CourseContent.course_rel),
        )
        .where(CourseContent.id == content_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise NotFoundError("Content", str(content_id))
    return content


async def require_content_owner_or_admin(
    content: CourseContent = Depends(get_content_or_404),
    current_user: User = Depends(get_current_user),
) -> CourseContent:
    if content.course_rel.owner_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise AppException(
            code="CONTENT_ACCESS_DENIED",
            message="You do not have permission to modify this content.",
            status_code=403,
        )
    return content
