import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppException, NotFoundError
from app.modules.auth.dependencies import get_current_user
from app.modules.files.repository import FileAssetRepository
from app.modules.files.schemas import FileAssetResponse
from app.modules.files.service import FileService
from app.modules.files.storage import LocalFileStorage
from app.modules.users.models import User

router = APIRouter(tags=["files"])


def _storage() -> LocalFileStorage:
    return LocalFileStorage(Path(settings.STORAGE_LOCAL_PATH))


@router.post("/upload", response_model=FileAssetResponse, status_code=201)
async def upload_file(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileAssetResponse:
    if not file.filename:
        raise AppException(code="MISSING_FILENAME", message="No filename provided.", status_code=422)
    data = await file.read()
    fa = await FileService(db, _storage()).upload(
        data=data,
        original_filename=file.filename,
        uploaded_by=current_user.id,
    )
    return FileAssetResponse.model_validate(fa)


@router.get("/{file_id}")
async def download_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    fa = await FileAssetRepository(db).get_by_id(file_id)
    if not fa:
        raise NotFoundError("File", str(file_id))
    storage = _storage()
    if not await FileService(db, storage).can_access(fa, current_user):
        raise AppException(
            code="FILE_ACCESS_DENIED",
            message="You do not have permission to access this file.",
            status_code=403,
        )
    file_path = storage.resolve_path(fa.storage_path)
    if not file_path.exists():
        raise AppException(
            code="FILE_NOT_FOUND_ON_STORAGE",
            message="File not found on storage.",
            status_code=404,
        )
    return FileResponse(path=str(file_path), filename=fa.original_filename, media_type=fa.mime_type)


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    fa = await FileAssetRepository(db).get_by_id(file_id)
    if not fa:
        raise NotFoundError("File", str(file_id))
    await FileService(db, _storage()).delete_asset(fa, current_user)
