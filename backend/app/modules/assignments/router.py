import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.assignments.repository import AssignmentRepository, EnrollmentRepository
from app.modules.assignments.schemas import (
    AssignmentResponse, CreateAssignmentRequest, EnrollmentResponse,
)
from app.modules.assignments.service import AssignmentService
from app.modules.users.models import User, UserRole

router = APIRouter()


@router.post("/assignments", response_model=AssignmentResponse, status_code=201, tags=["assignments"])
async def create_assignment(body: CreateAssignmentRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)) -> AssignmentResponse:
    assignment = await AssignmentService(db).create(
        user_id=body.user_id,
        assigned_by=current_user.id,
        target_type=body.target_type,
        target_id=body.target_id,
        starts_at=body.starts_at,
        due_date=body.due_date,
    )
    return AssignmentResponse.model_validate(assignment)


@router.get("/assignments", response_model=list[AssignmentResponse], tags=["assignments"])
async def list_assignments(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)) -> list[AssignmentResponse]:
    assignments = await AssignmentRepository(db).get_all()
    return [AssignmentResponse.model_validate(a) for a in assignments]


@router.get("/assignments/{assignment_id}", response_model=AssignmentResponse, tags=["assignments"])
async def get_assignment(assignment_id: uuid.UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)) -> AssignmentResponse:
    a = await AssignmentRepository(db).get_by_id(assignment_id)
    if not a:
        raise NotFoundError("Assignment", str(assignment_id))
    return AssignmentResponse.model_validate(a)


@router.delete("/assignments/{assignment_id}", status_code=204, tags=["assignments"])
async def cancel_assignment(assignment_id: uuid.UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)) -> None:
    a = await AssignmentRepository(db).get_by_id(assignment_id)
    if not a:
        raise NotFoundError("Assignment", str(assignment_id))
    await AssignmentService(db).cancel(a)


# ── Enrollments ─────────────────────────────────────────────────────────────

@router.get("/enrollments", response_model=list[EnrollmentResponse], tags=["enrollments"])
async def list_enrollments(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[EnrollmentResponse]:
    repo = EnrollmentRepository(db)
    if current_user.role == UserRole.ADMIN:
        enrollments = await repo.get_all()
    else:
        enrollments = await repo.get_for_user(current_user.id)
    return [EnrollmentResponse.model_validate(e) for e in enrollments]


@router.get("/enrollments/{enrollment_id}", response_model=EnrollmentResponse, tags=["enrollments"])
async def get_enrollment(enrollment_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> EnrollmentResponse:
    e = await EnrollmentRepository(db).get_by_id(enrollment_id)
    if not e:
        raise NotFoundError("Enrollment", str(enrollment_id))
    if e.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise NotFoundError("Enrollment", str(enrollment_id))
    return EnrollmentResponse.model_validate(e)
