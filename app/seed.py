from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.database import SessionLocal, create_tables
from app.models import Category, Expense


SEED_EXPENSES = [
    ("Groceries", "1450.50", date(2026, 3, 2), "Food"),
    ("Metro card", "800.00", date(2026, 3, 4), "Transport"),
    ("March rent", "16000.00", date(2026, 3, 5), "Rent"),
    ("Movie tickets", "650.00", date(2026, 3, 8), "Fun"),
    ("Electricity bill", "1325.75", date(2026, 3, 12), "Utilities"),
    ("Restaurant dinner", "2200.00", date(2026, 3, 21), "Food"),
    ("Vegetables", "920.25", date(2026, 4, 1), "Food"),
    ("Cab ride", "475.00", date(2026, 4, 3), "Transport"),
    ("April rent", "16000.00", date(2026, 4, 5), "Rent"),
    ("Bowling", "1100.00", date(2026, 4, 11), "Fun"),
    ("Internet bill", "999.00", date(2026, 4, 15), "Utilities"),
    ("Fuel", "2500.00", date(2026, 4, 24), "Transport"),
]


def seed_database() -> None:
    create_tables()

    with SessionLocal() as database:
        category_count = database.scalar(select(func.count(Category.id)))
        expense_count = database.scalar(select(func.count(Expense.id)))

        if category_count or expense_count:
            print("Seed skipped: the database already contains data.")
            return

        categories = {
            name: Category(name=name)
            for name in ["Food", "Transport", "Rent", "Fun", "Utilities"]
        }
        database.add_all(categories.values())
        database.flush()

        database.add_all(
            [
                Expense(
                    description=description,
                    amount=Decimal(amount),
                    spent_on=spent_on,
                    category_id=categories[category_name].id,
                )
                for description, amount, spent_on, category_name in SEED_EXPENSES
            ]
        )
        database.commit()

    print("Seeded 5 categories and 12 expenses.")


if __name__ == "__main__":
    seed_database()

