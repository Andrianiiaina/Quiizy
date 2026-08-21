import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.contents.models import ContentType


class FileAssetSummary(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    original_filename: str
    mime_type: str
    size_bytes: int


class ContentResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    course_id: uuid.UUID
    type: ContentType
    title: str
    text_content: str | None
    file_asset_id: uuid.UUID | None
    file_asset: FileAssetSummary | None = None
    external_url: str | None
    position: int
    created_at: datetime
    updated_at: datetime


class CreateContentRequest(BaseModel):
    type: ContentType
    title: str = Field(min_length=1, max_length=255, strip_whitespace=True)
    text_content: str | None = None
    file_asset_id: uuid.UUID | None = None
    external_url: str | None = None


class UpdateContentRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255, strip_whitespace=True)
    text_content: str | None = None
    file_asset_id: uuid.UUID | None = None
    external_url: str | None = None


class ReorderItem(BaseModel):
    id: uuid.UUID
    position: int = Field(ge=0)
