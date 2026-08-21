import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.modules.progress.models import ProgressStatus


class ContentProgressResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    enrollment_id: uuid.UUID
    content_id: uuid.UUID
    status: ProgressStatus
    progress_percent: int
    last_position: str | None
    completed_at: datetime | None


class UpdateProgressRequest(BaseModel):
    status: ProgressStatus
    progress_percent: int = Field(ge=0, le=100, default=0)
    last_position: str | None = None
