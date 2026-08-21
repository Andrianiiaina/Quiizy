import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.files.models import FileAsset


class FileAssetRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, file_id: uuid.UUID) -> FileAsset | None:
        result = await self._db.execute(select(FileAsset).where(FileAsset.id == file_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        original_filename: str,
        stored_filename: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
        uploaded_by: uuid.UUID,
        storage_backend: str = "LOCAL",
    ) -> FileAsset:
        fa = FileAsset(
            original_filename=original_filename,
            stored_filename=stored_filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            uploaded_by=uploaded_by,
            storage_backend=storage_backend,
        )
        self._db.add(fa)
        await self._db.flush()
        await self._db.refresh(fa)
        return fa

    async def delete(self, fa: FileAsset) -> None:
        await self._db.delete(fa)
        await self._db.flush()
