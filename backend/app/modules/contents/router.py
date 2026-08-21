import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.contents.dependencies import get_content_or_404, require_content_owner_or_admin
from app.modules.contents.models import CourseContent
from app.modules.contents.repository import ContentRepository
from app.modules.contents.schemas import (
    ContentResponse,
    CreateContentRequest,
    ReorderItem,
    UpdateContentRequest,
)
from app.modules.contents.service import ContentService
from app.modules.courses.dependencies import require_course_owner_or_admin
from app.modules.courses.models import Course
from app.modules.users.models import User

router = APIRouter()

_TAGS = ["contents"]


@router.get("/courses/{course_id}/contents", response_model=list[ContentResponse], tags=_TAGS)
async def list_contents(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ContentResponse]:
    contents = await ContentRepository(db).list_for_course(course_id)
    return [ContentResponse.model_validate(c) for c in contents]


@router.post("/courses/{course_id}/contents", response_model=ContentResponse, status_code=201, tags=_TAGS)
async def create_content(
    body: CreateContentRequest,
    db: AsyncSession = Depends(get_db),
    course: Course = Depends(require_course_owner_or_admin),
) -> ContentResponse:
    content = await ContentService(db).create(
        course_id=course.id,
        content_type=body.type,
        title=body.title,
        text_content=body.text_content,
        file_asset_id=body.file_asset_id,
        external_url=body.external_url,
    )
    return ContentResponse.model_validate(content)


@router.patch("/courses/{course_id}/contents/reorder", status_code=204, tags=_TAGS)
async def reorder_contents(
    course_id: uuid.UUID,
    items: list[ReorderItem],
    db: AsyncSession = Depends(get_db),
    course: Course = Depends(require_course_owner_or_admin),
) -> None:
    await ContentService(db).reorder(course.id, items)


@router.get("/contents/{content_id}", response_model=ContentResponse, tags=_TAGS)
async def get_content(
    content: CourseContent = Depends(get_content_or_404),
    _: User = Depends(get_current_user),
) -> ContentResponse:
    return ContentResponse.model_validate(content)


@router.patch("/contents/{content_id}", response_model=ContentResponse, tags=_TAGS)
async def update_content(
    body: UpdateContentRequest,
    db: AsyncSession = Depends(get_db),
    content: CourseContent = Depends(require_content_owner_or_admin),
) -> ContentResponse:
    updated = await ContentService(db).update(content, data=body.model_dump(exclude_unset=True))
    return ContentResponse.model_validate(updated)


@router.delete("/contents/{content_id}", status_code=204, tags=_TAGS)
async def delete_content(
    db: AsyncSession = Depends(get_db),
    content: CourseContent = Depends(require_content_owner_or_admin),
) -> None:
    await ContentService(db).delete(content)
