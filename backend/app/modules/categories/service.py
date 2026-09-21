from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.categories.models import Category
from app.modules.categories.repository import CategoryRepository


class CategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = CategoryRepository(db)

    async def create(self, *, name: str, description: str | None) -> Category:
        if await self._repo.get_by_name(name):
            raise AppException(
                code="CATEGORY_ALREADY_EXISTS",
                message=f"Category '{name}' already exists.",
                status_code=409,
            )
        cat = await self._repo.create(name=name, description=description)
        await self._db.commit()
        return cat

    async def update(self, cat: Category, *, data: dict) -> Category:
        if "name" in data and data["name"]:
            existing = await self._repo.get_by_name(data["name"])
            if existing and existing.id != cat.id:
                raise AppException(
                    code="CATEGORY_ALREADY_EXISTS",
                    message=f"Category '{data['name']}' already exists.",
                    status_code=409,
                )
        cat = await self._repo.update(cat, data=data)
        await self._db.commit()
        return cat

    async def delete(self, cat: Category) -> None:
        await self._repo.delete(cat)
        await self._db.commit()
