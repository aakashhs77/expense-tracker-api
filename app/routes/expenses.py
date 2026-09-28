from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Category, Expense
from app.schemas import ExpenseInput, ExpenseResponse


router = APIRouter(prefix="/expenses", tags=["expenses"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def expense_query() -> Select[tuple[Expense]]:
    return select(Expense).options(joinedload(Expense.category))


def find_expense_or_404(expense_id: int, database: Session) -> Expense:
    expense = database.scalar(
        expense_query().where(Expense.id == expense_id)
    )
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

    statement = expense_query()

    if category_id is not None:
        statement = statement.where(Expense.category_id == category_id)
    if from_date is not None:
        statement = statement.where(Expense.spent_on >= from_date)
    if to_date is not None:
        statement = statement.where(Expense.spent_on <= to_date)

    statement = statement.order_by(Expense.spent_on, Expense.id)
    return list(database.scalars(statement))


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
    expense = Expense(
        amount=expense_input.amount,
        description=expense_input.description,
        spent_on=expense_input.spent_on,
        category=category,
    )
    database.add(expense)
    database.commit()
    return expense


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_input: ExpenseInput,
    database: DatabaseSession,
) -> Expense:
    expense = find_expense_or_404(expense_id, database)
    category = find_category_or_422(expense_input.category_id, database)

    expense.amount = expense_input.amount
    expense.description = expense_input.description
    expense.spent_on = expense_input.spent_on
    expense.category = category
    database.commit()
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, database: DatabaseSession) -> Response:
    expense = find_expense_or_404(expense_id, database)
    database.delete(expense)
    database.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

