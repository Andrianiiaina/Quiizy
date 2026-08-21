import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.courses.models import CourseStatus


class CategorySummary(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    name: str


class CourseResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    owner_id: uuid.UUID
    category_id: uuid.UUID | None
    category: CategorySummary | None = None
    cover_image_id: uuid.UUID | None = None
    title: str
    description: str | None
    status: CourseStatus
    created_at: datetime
    updated_at: datetime


class CreateCourseRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255, strip_whitespace=True)
    description: str | None = None
    category_id: uuid.UUID | None = None


class UpdateCourseRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255, strip_whitespace=True)
    description: str | None = None
    category_id: uuid.UUID | None = None
