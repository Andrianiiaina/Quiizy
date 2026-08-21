import uuid
from datetime import datetime

from pydantic import BaseModel


class FileAssetResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    original_filename: str
    mime_type: str
    size_bytes: int
    created_at: datetime
