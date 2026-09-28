from datetime import date
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models import Category, Expense


def expense_query() -> Select[tuple[Expense]]:
    return select(Expense).options(joinedload(Expense.category))


def fetch_expenses(
    database: Session,
    *,
    category_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[Expense]:
    statement = expense_query()

    if category_id is not None:
        statement = statement.where(Expense.category_id == category_id)
    if from_date is not None:
        statement = statement.where(Expense.spent_on >= from_date)
    if to_date is not None:
        statement = statement.where(Expense.spent_on <= to_date)

    statement = statement.order_by(Expense.spent_on, Expense.id)
    return list(database.scalars(statement))


def fetch_expense(database: Session, expense_id: int) -> Expense | None:
    return database.scalar(
        expense_query().where(Expense.id == expense_id)
    )


def create_expense_record(
    database: Session,
    *,
    amount: Decimal,
    description: str,
    spent_on: date,
    category: Category,
) -> Expense:
    expense = Expense(
        amount=amount,
        description=description,
        spent_on=spent_on,
        category=category,
    )
    database.add(expense)
    database.commit()
    return expense


def update_expense_record(
    database: Session,
    expense: Expense,
    *,
    amount: Decimal,
    description: str,
    spent_on: date,
    category: Category,
) -> Expense:
    expense.amount = amount
    expense.description = description
    expense.spent_on = spent_on
    expense.category = category
    database.commit()
    return expense


def delete_expense_record(database: Session, expense: Expense) -> None:
    database.delete(expense)
    database.commit()
