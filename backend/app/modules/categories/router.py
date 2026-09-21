import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.categories.repository import CategoryRepository
from app.modules.categories.schemas import (
    CategoryResponse,
    CreateCategoryRequest,
    UpdateCategoryRequest,
)
from app.modules.categories.service import CategoryService
from app.modules.users.models import User

router = APIRouter(tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CategoryResponse]:
    cats = await CategoryRepository(db).get_all()
    return [CategoryResponse.model_validate(c) for c in cats]


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    body: CreateCategoryRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CategoryResponse:
    # Toute personne authentifiée peut créer une catégorie (ex. depuis le formulaire de cours) —
    # seules la modification et la suppression restent réservées aux ADMIN.
    cat = await CategoryService(db).create(name=body.name, description=body.description)
    return CategoryResponse.model_validate(cat)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CategoryResponse:
    cat = await CategoryRepository(db).get_by_id(category_id)
    if not cat:
        raise NotFoundError("Category", str(category_id))
    return CategoryResponse.model_validate(cat)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    body: UpdateCategoryRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> CategoryResponse:
    repo = CategoryRepository(db)
    cat = await repo.get_by_id(category_id)
    if not cat:
        raise NotFoundError("Category", str(category_id))
    data = body.model_dump(exclude_unset=True)
    cat = await CategoryService(db).update(cat, data=data)
    return CategoryResponse.model_validate(cat)


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    repo = CategoryRepository(db)
    cat = await repo.get_by_id(category_id)
    if not cat:
        raise NotFoundError("Category", str(category_id))
    await CategoryService(db).delete(cat)

