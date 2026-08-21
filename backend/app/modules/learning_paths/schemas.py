import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.modules.learning_paths.models import LPStatus


class CourseSummary(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    title: str
    status: str


class LPCourseItem(BaseModel):
    model_config = {"from_attributes": True}
    course_id: uuid.UUID
    position: int


class LPResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    created_by: uuid.UUID
    title: str
    description: str | None
    status: LPStatus
    created_at: datetime
    updated_at: datetime


class CreateLPRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255, strip_whitespace=True)
    description: str | None = None


class UpdateLPRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255, strip_whitespace=True)
    description: str | None = None


class AddCourseRequest(BaseModel):
    course_id: uuid.UUID


class ReorderCourseItem(BaseModel):
    course_id: uuid.UUID
    position: int = Field(ge=0)
