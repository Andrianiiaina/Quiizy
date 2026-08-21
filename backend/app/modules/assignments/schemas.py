import uuid
from datetime import datetime
from pydantic import BaseModel
from app.modules.assignments.models import AssignmentTargetType, AssignmentStatus, EnrollmentStatus


class AssignmentResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    user_id: uuid.UUID
    assigned_by: uuid.UUID
    target_type: AssignmentTargetType
    target_id: uuid.UUID
    starts_at: datetime | None
    due_date: datetime | None
    status: AssignmentStatus
    created_at: datetime


class CreateAssignmentRequest(BaseModel):
    user_id: uuid.UUID
    target_type: AssignmentTargetType
    target_id: uuid.UUID
    starts_at: datetime | None = None
    due_date: datetime | None = None


class EnrollmentResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    user_id: uuid.UUID
    assignment_id: uuid.UUID
    course_id: uuid.UUID
    learning_path_id: uuid.UUID | None
    status: EnrollmentStatus
    progress_percent: int
    started_at: datetime | None
    completed_at: datetime | None
    due_date: datetime | None
    created_at: datetime
