from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Expense
from app.schemas import ExpenseInput, ExpenseResponse
from app.services.expenses import (
    create_expense_record,
    delete_expense_record,
    fetch_expense,
    fetch_expenses,
    update_expense_record,
)


router = APIRouter(prefix="/expenses", tags=["expenses"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def find_expense_or_404(expense_id: int, database: Session) -> Expense:
    expense = fetch_expense(database, expense_id)
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found.",
        )
    return expense


def find_category_or_422(category_id: int, database: Session) -> Category:
    category = database.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Category does not exist.",
        )
    return category


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    database: DatabaseSession,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[Expense]:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date must be on or before to_date.",
        )

    return fetch_expenses(
        database,
        category_id=category_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, database: DatabaseSession) -> Expense:
    return find_expense_or_404(expense_id, database)


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_expense(
    expense_input: ExpenseInput,
    database: DatabaseSession,
) -> Expense:
    category = find_category_or_422(expense_input.category_id, database)
    return create_expense_record(
        database,
        expense_input=expense_input,
        category=category,
    )


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_input: ExpenseInput,
    database: DatabaseSession,
) -> Expense:
    expense = find_expense_or_404(expense_id, database)
    category = find_category_or_422(expense_input.category_id, database)

    return update_expense_record(
        database,
        expense,
        expense_input=expense_input,
        category=category,
    )


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, database: DatabaseSession) -> Response:
    expense = find_expense_or_404(expense_id, database)
    delete_expense_record(database, expense)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
