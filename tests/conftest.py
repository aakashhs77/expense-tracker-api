import os
from collections.abc import Generator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker


os.environ["EXPENSE_TRACKER_DATABASE_URL"] = (
    "sqlite:///./test_expense_tracker.db"
)

from app.database import Base, engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Category, Expense  # noqa: E402


TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def override_get_db() -> Generator[Session, None, None]:
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


@pytest.fixture(autouse=True)
def reset_test_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as database:
        food = Category(name="Food")
        transport = Category(name="Transport")
        rent = Category(name="Rent")
        database.add_all([food, transport, rent])
        database.flush()

        database.add_all(
            [
                Expense(
                    amount=Decimal("12.50"),
                    description="Lunch",
                    spent_on=date(2026, 3, 5),
                    category=food,
                ),
                Expense(
                    amount=Decimal("37.50"),
                    description="Groceries",
                    spent_on=date(2026, 3, 10),
                    category=food,
                ),
                Expense(
                    amount=Decimal("10.00"),
                    description="Bus",
                    spent_on=date(2026, 3, 8),
                    category=transport,
                ),
                Expense(
                    amount=Decimal("20.00"),
                    description="April lunch",
                    spent_on=date(2026, 4, 2),
                    category=food,
                ),
            ]
        )
        database.commit()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
