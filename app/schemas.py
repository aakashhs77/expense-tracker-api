from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ExpenseInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    description: str = Field(min_length=1, max_length=255)
    spent_on: date
    category_id: int = Field(gt=0)


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    description: str
    spent_on: date
    category_id: int
    category: CategoryResponse


class CategorySummaryResponse(BaseModel):
    category_name: str
    total: Decimal
    share_percentage: Decimal


class MonthlySummaryResponse(BaseModel):
    month: str
    total_spend: Decimal
    categories: list[CategorySummaryResponse]

