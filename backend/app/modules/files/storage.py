from abc import ABC, abstractmethod
from pathlib import Path


class FileStorage(ABC):
    @abstractmethod
    async def save(self, data: bytes, stored_filename: str) -> str: ...

    @abstractmethod
    def resolve_path(self, storage_path: str) -> Path: ...

    @abstractmethod
    async def delete(self, storage_path: str) -> None: ...


class LocalFileStorage(FileStorage):
    def __init__(self, base_path: Path) -> None:
        self._base = base_path
        self._base.mkdir(parents=True, exist_ok=True)

    async def save(self, data: bytes, stored_filename: str) -> str:
        dest = self._base / stored_filename
        dest.write_bytes(data)
        return stored_filename  # storage_path == stored_filename for LOCAL

    def resolve_path(self, storage_path: str) -> Path:
        return self._base / storage_path

    async def delete(self, storage_path: str) -> None:
        path = self._base / storage_path
        if path.exists():
            path.unlink()
