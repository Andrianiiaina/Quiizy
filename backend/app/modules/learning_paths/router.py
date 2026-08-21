import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException, NotFoundError
from app.core.pagination import PaginatedResponse
from app.modules.auth.dependencies import get_current_user
from app.modules.learning_paths.models import LearningPath, LPStatus
from app.modules.learning_paths.repository import LPRepository
from app.modules.learning_paths.schemas import (
    AddCourseRequest, CreateLPRequest, LPCourseItem,
    LPResponse, ReorderCourseItem, UpdateLPRequest,
)
from app.modules.learning_paths.service import LPService
from app.modules.users.models import User, UserRole

router = APIRouter(tags=["learning-paths"])


def _check_owner(lp: LearningPath, user: User) -> None:
    if lp.created_by != user.id and user.role != UserRole.ADMIN:
        raise AppException(code="LP_ACCESS_DENIED", message="You do not have permission to modify this learning path.", status_code=403)


@router.get("", response_model=PaginatedResponse[LPResponse])
async def list_lps(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> PaginatedResponse[LPResponse]:
    lps, total = await LPRepository(db).get_all(current_user_id=current_user.id, is_admin=current_user.role == UserRole.ADMIN, page=page, per_page=per_page)
    return PaginatedResponse(items=[LPResponse.model_validate(lp) for lp in lps], total=total, page=page, per_page=per_page)


@router.post("", response_model=LPResponse, status_code=201)
async def create_lp(body: CreateLPRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> LPResponse:
    lp = await LPService(db).create(created_by=current_user.id, title=body.title, description=body.description)
    return LPResponse.model_validate(lp)


@router.get("/{lp_id}", response_model=LPResponse)
async def get_lp(lp_id: uuid.UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> LPResponse:
    lp = await LPRepository(db).get_by_id(lp_id)
    if not lp:
        raise NotFoundError("LearningPath", str(lp_id))
    return LPResponse.model_validate(lp)


@router.get("/{lp_id}/courses", response_model=list[LPCourseItem])
async def get_lp_courses(lp_id: uuid.UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)) -> list[LPCourseItem]:
    courses = await LPRepository(db).get_courses(lp_id)
    return [LPCourseItem.model_validate(c) for c in courses]


@router.patch("/{lp_id}", response_model=LPResponse)
async def update_lp(lp_id: uuid.UUID, body: UpdateLPRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> LPResponse:
    lp = await LPRepository(db).get_by_id(lp_id)
    if not lp:
        raise NotFoundError("LearningPath", str(lp_id))
    _check_owner(lp, current_user)
    updated = await LPService(db).update(lp, body.model_dump(exclude_unset=True))
    return LPResponse.model_validate(updated)


@router.delete("/{lp_id}", status_code=204)
async def delete_lp(lp_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    lp = await LPRepository(db).get_by_id(lp_id)
    if not lp:
        raise NotFoundError("LearningPath", str(lp_id))
    _check_owner(lp, current_user)
    await LPService(db).delete(lp)


@router.patch("/{lp_id}/publish", response_model=LPResponse)
async def publish_lp(lp_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> LPResponse:
    lp = await LPRepository(db).get_by_id(lp_id)
    if not lp:
        raise NotFoundError("LearningPath", str(lp_id))
    _check_owner(lp, current_user)
    return LPResponse.model_validate(await LPService(db).set_status(lp, LPStatus.PUBLISHED))


@router.patch("/{lp_id}/archive", response_model=LPResponse)
async def archive_lp(lp_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> LPResponse:
    lp = await LPRepository(db).get_by_id(lp_id)
    if not lp:
        raise NotFoundError("LearningPath", str(lp_id))
    _check_owner(lp, current_user)
    return LPResponse.model_validate(await LPService(db).set_status(lp, LPStatus.ARCHIVED))


@router.post("/{lp_id}/courses", status_code=201)
async def add_course_to_lp(lp_id: uuid.UUID, body: AddCourseRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    lp = await LPRepository(db).get_by_id(lp_id)
    if not lp:
        raise NotFoundError("LearningPath", str(lp_id))
    _check_owner(lp, current_user)
    await LPService(db).add_course(lp, body.course_id)
    return {"ok": True}


@router.delete("/{lp_id}/courses/{course_id}", status_code=204)
async def remove_course_from_lp(lp_id: uuid.UUID, course_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    lp = await LPRepository(db).get_by_id(lp_id)
    if not lp:
        raise NotFoundError("LearningPath", str(lp_id))
    _check_owner(lp, current_user)
    await LPService(db).remove_course(lp, course_id)


@router.patch("/{lp_id}/courses/reorder", status_code=204)
async def reorder_lp_courses(lp_id: uuid.UUID, items: list[ReorderCourseItem], db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    lp = await LPRepository(db).get_by_id(lp_id)
    if not lp:
        raise NotFoundError("LearningPath", str(lp_id))
    _check_owner(lp, current_user)
    await LPService(db).reorder_courses(lp, items)
