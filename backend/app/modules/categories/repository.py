import uuid

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.models import Category


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all(self) -> list[Category]:
        result = await self._db.execute(select(Category).order_by(Category.name))
        return list(result.scalars().all())

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        result = await self._db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Category | None:
        result = await self._db.execute(
            select(Category).where(sa.func.lower(Category.name) == name.lower().strip())
        )
        return result.scalar_one_or_none()

    async def create(self, *, name: str, description: str | None) -> Category:
        cat = Category(name=name.strip(), description=description)
        self._db.add(cat)
        await self._db.flush()
        await self._db.refresh(cat)
        return cat

    async def update(self, cat: Category, *, data: dict) -> Category:
        for key, value in data.items():
            setattr(cat, key, value)
        await self._db.flush()
        await self._db.refresh(cat)
        return cat

    async def delete(self, cat: Category) -> None:
        await self._db.delete(cat)
        await self._db.flush()
