import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category, Expense
from app.schemas import CategorySummaryResponse, MonthlySummaryResponse


router = APIRouter(tags=["summary"])
DatabaseSession = Annotated[Session, Depends(get_db)]
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
PERCENTAGE_PRECISION = Decimal("0.01")


def parse_month(month: str | None) -> tuple[date, date]:
    if month is None or not MONTH_PATTERN.fullmatch(month):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="month is required and must use the YYYY-MM format.",
        )

    year, month_number = (int(value) for value in month.split("-"))
    try:
        month_start = date(year, month_number, 1)

        if month_number == 12:
            next_month_start = date(year + 1, 1, 1)
        else:
            next_month_start = date(year, month_number + 1, 1)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="month is required and must use the YYYY-MM format.",
        ) from error

    return month_start, next_month_start


@router.get("/summary", response_model=MonthlySummaryResponse)
def get_monthly_summary(
    database: DatabaseSession,
    month: Annotated[
        str | None,
        Query(description="Month in YYYY-MM format"),
    ] = None,
) -> MonthlySummaryResponse:
    month_start, next_month_start = parse_month(month)

    category_total = func.sum(Expense.amount).label("category_total")
    statement = (
        select(Category.name, category_total)
        .join(Expense, Expense.category_id == Category.id)
        .where(
            Expense.spent_on >= month_start,
            Expense.spent_on < next_month_start,
        )
        .group_by(Category.id, Category.name)
        .order_by(Category.name)
    )
    rows = database.execute(statement).all()
    total_spend = sum(
        (row.category_total for row in rows),
        start=Decimal("0.00"),
    )

    categories = [
        CategorySummaryResponse(
            category_name=row.name,
            total=row.category_total,
            share_percentage=(
                (row.category_total / total_spend * Decimal("100")).quantize(
                    PERCENTAGE_PRECISION,
                    rounding=ROUND_HALF_UP,
                )
            ),
        )
        for row in rows
    ]

    return MonthlySummaryResponse(
        month=month,
        total_spend=total_spend,
        categories=categories,
    )
