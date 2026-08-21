from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import PaginatedResponse
from app.modules.auth.dependencies import get_current_user
from app.modules.courses.dependencies import (
    get_visible_course_or_404,
    require_course_owner_or_admin,
)
from app.modules.courses.models import Course
from app.modules.courses.repository import CourseRepository
from app.modules.courses.schemas import CourseResponse, CreateCourseRequest, UpdateCourseRequest
from app.modules.courses.service import CourseService
from app.modules.users.models import User

router = APIRouter(tags=["courses"])


@router.get("", response_model=PaginatedResponse[CourseResponse])
async def list_courses(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[CourseResponse]:
    courses, total = await CourseRepository(db).get_all(
        current_user=current_user, page=page, per_page=per_page
    )
    return PaginatedResponse(
        items=[CourseResponse.model_validate(c) for c in courses],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=CourseResponse, status_code=201)
async def create_course(
    body: CreateCourseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourseResponse:
    course = await CourseService(db).create(
        owner_id=current_user.id,
        title=body.title,
        description=body.description,
        category_id=body.category_id,
    )
    return CourseResponse.model_validate(course)


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course: Course = Depends(get_visible_course_or_404),
) -> CourseResponse:
    return CourseResponse.model_validate(course)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    body: UpdateCourseRequest,
    db: AsyncSession = Depends(get_db),
    course: Course = Depends(require_course_owner_or_admin),
) -> CourseResponse:
    updated = await CourseService(db).update(course, data=body.model_dump(exclude_unset=True))
    return CourseResponse.model_validate(updated)


@router.delete("/{course_id}", status_code=204)
async def delete_course(
    db: AsyncSession = Depends(get_db),
    course: Course = Depends(require_course_owner_or_admin),
) -> None:
    await CourseService(db).delete(course)


@router.patch("/{course_id}/publish", response_model=CourseResponse)
async def publish_course(
    db: AsyncSession = Depends(get_db),
    course: Course = Depends(require_course_owner_or_admin),
) -> CourseResponse:
    return CourseResponse.model_validate(await CourseService(db).publish(course))


@router.patch("/{course_id}/archive", response_model=CourseResponse)
async def archive_course(
    db: AsyncSession = Depends(get_db),
    course: Course = Depends(require_course_owner_or_admin),
) -> CourseResponse:
    return CourseResponse.model_validate(await CourseService(db).archive(course))
