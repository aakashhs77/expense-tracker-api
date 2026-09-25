from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Expense
from app.schemas import CategoryInput, CategoryResponse


router = APIRouter(prefix="/categories", tags=["categories"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def find_category_or_404(category_id: int, database: Session) -> Category:
    category = database.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )
    return category


def commit_category_or_409(
    category: Category,
    database: Session,
) -> Category:
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name already exists.",
        ) from error

    database.refresh(category)
    return category


@router.get("", response_model=list[CategoryResponse])
def list_categories(database: DatabaseSession) -> list[Category]:
    statement = select(Category).order_by(Category.id)
    return list(database.scalars(statement))


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, database: DatabaseSession) -> Category:
    return find_category_or_404(category_id, database)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    category_input: CategoryInput,
    database: DatabaseSession,
) -> Category:
    category = Category(name=category_input.name)
    database.add(category)
    return commit_category_or_409(category, database)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_input: CategoryInput,
    database: DatabaseSession,
) -> Category:
    category = find_category_or_404(category_id, database)
    category.name = category_input.name
    return commit_category_or_409(category, database)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, database: DatabaseSession) -> Response:
    category = find_category_or_404(category_id, database)
    expense_count = database.scalar(
        select(func.count(Expense.id)).where(Expense.category_id == category_id)
    )

    if expense_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category cannot be deleted while it has expenses.",
        )

    database.delete(category)
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category cannot be deleted while it has expenses.",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)

