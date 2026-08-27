import uuid

from app.core.exceptions import AccessDeniedError
from app.modules.users.models import User, UserRole


def require_ownership_or_admin(owner_id: uuid.UUID, current_user: User) -> None:
    """Raise 403 if current_user is not the resource owner and not ADMIN."""
    if current_user.role != UserRole.ADMIN and current_user.id != owner_id:
        raise AccessDeniedError()
