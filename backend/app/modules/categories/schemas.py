import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime


class CreateCategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, strip_whitespace=True)
    description: str | None = None


class UpdateCategoryRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100, strip_whitespace=True)
    description: str | None = None
