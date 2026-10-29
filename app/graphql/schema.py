from datetime import date
from decimal import Decimal
from typing import Annotated, TypedDict

import strawberry
from fastapi import Depends
from graphql import GraphQLError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from strawberry.dataloader import DataLoader
from strawberry.types import Info

from app.database import get_db
from app.models import Category, Expense
from app.schemas import ExpenseInput as ExpenseValidationInput
from app.services.expenses import (
    create_expense_record,
    delete_expense_record,
    fetch_expense,
    fetch_expenses,
)


@strawberry.type(name="ExpenseCategory")
class ExpenseCategoryType:
    id: int
    name: str


@strawberry.type(name="Expense")
class ExpenseType:
    id: int
    amount: Decimal
    description: str
    spent_on: date
    category: ExpenseCategoryType


@strawberry.type(name="CategoryExpense")
class CategoryExpenseType:
    id: int
    amount: Decimal
    description: str
    spent_on: date


@strawberry.type(name="Category")
class CategoryType:
    id: int
    name: str

    @strawberry.field
    async def expenses(
        self,
        info: Info["GraphQLContext", None],
    ) -> list[CategoryExpenseType]:
        return await info.context["category_expenses"].load(self.id)


@strawberry.input
class AddExpenseInput:
    amount: Decimal
    description: str
    spent_on: date
    category_id: int


class GraphQLContext(TypedDict):
    database: Session
    category_expenses: DataLoader[int, list[CategoryExpenseType]]


async def get_graphql_context(
    database: Annotated[Session, Depends(get_db)],
) -> GraphQLContext:
    async def load_category_expenses(
        category_ids: list[int],
    ) -> list[list[CategoryExpenseType]]:
        return await run_in_threadpool(
            load_expenses_by_category, database, category_ids,
        )

    return {
        "database": database,
        # Keep batching, but avoid stale results after mutations in the same request.
        "category_expenses": DataLoader(load_fn=load_category_expenses, cache=False),
    }


def expense_to_graphql(expense: Expense) -> ExpenseType:
    return ExpenseType(
        id=expense.id,
        amount=expense.amount,
        description=expense.description,
        spent_on=expense.spent_on,
        category=ExpenseCategoryType(
            id=expense.category.id,
            name=expense.category.name,
        ),
    )


def load_expenses_by_category(
    database: Session,
    category_ids: list[int],
) -> list[list[CategoryExpenseType]]:
    # Batch all requested categories, including categories with no expenses.
    grouped: dict[int, list[CategoryExpenseType]] = {
        category_id: [] for category_id in category_ids
    }
    statement = (
        select(Expense)
        .where(Expense.category_id.in_(category_ids))
        .order_by(Expense.spent_on, Expense.id)
    )
    for expense in database.scalars(statement):
        grouped[expense.category_id].append(
            CategoryExpenseType(
                id=expense.id,
                amount=expense.amount,
                description=expense.description,
                spent_on=expense.spent_on,
            )
        )
    return [grouped[category_id] for category_id in category_ids]


def load_expenses(
    database: Session,
    category_id: int | None,
    from_date: date | None,
    to_date: date | None,
) -> list[ExpenseType]:
    expenses = fetch_expenses(
        database,
        category_id=category_id,
        from_date=from_date,
        to_date=to_date,
    )
    return [expense_to_graphql(expense) for expense in expenses]


def load_categories(database: Session) -> list[CategoryType]:
    categories = database.scalars(select(Category).order_by(Category.id))
    return [CategoryType(id=category.id, name=category.name) for category in categories]


def add_expense(
    database: Session,
    expense_input: AddExpenseInput,
) -> ExpenseType:
    try:
        validated_input = ExpenseValidationInput(
            amount=expense_input.amount,
            description=expense_input.description,
            spent_on=expense_input.spent_on,
            category_id=expense_input.category_id,
        )
    except ValidationError as error:
        messages = "; ".join(
            detail["msg"] for detail in error.errors()
        )
        raise GraphQLError(messages) from error

    category = database.get(Category, validated_input.category_id)
    if category is None:
        raise GraphQLError("Category does not exist.")

    expense = create_expense_record(
        database,
        expense_input=validated_input,
        category=category,
    )
    return expense_to_graphql(expense)


def remove_expense(database: Session, expense_id: int) -> bool:
    expense = fetch_expense(database, expense_id)
    if expense is None:
        raise GraphQLError("Expense not found.")

    delete_expense_record(database, expense)
    return True


@strawberry.type
class Query:
    @strawberry.field
    async def expenses(
        self,
        info: Info[GraphQLContext, None],
        category_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[ExpenseType]:
        if category_id is not None and category_id <= 0:
            raise GraphQLError("categoryId must be greater than zero.")
        if from_date and to_date and from_date > to_date:
            raise GraphQLError("fromDate must be on or before toDate.")

        return await run_in_threadpool(
            load_expenses,
            info.context["database"],
            category_id,
            from_date,
            to_date,
        )

    @strawberry.field
    async def categories(
        self,
        info: Info[GraphQLContext, None],
    ) -> list[CategoryType]:
        return await run_in_threadpool(
            load_categories,
            info.context["database"],
        )


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def add_expense(
        self,
        info: Info[GraphQLContext, None],
        input: AddExpenseInput,
    ) -> ExpenseType:
        return await run_in_threadpool(
            add_expense,
            info.context["database"],
            input,
        )

    @strawberry.mutation
    async def delete_expense(
        self,
        info: Info[GraphQLContext, None],
        id: int,
    ) -> bool:
        if id <= 0:
            raise GraphQLError("id must be greater than zero.")
        return await run_in_threadpool(
            remove_expense,
            info.context["database"],
            id,
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
