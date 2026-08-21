import uuid
from datetime import datetime

from pydantic import BaseModel

from app.modules.users.models import UserRole


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
