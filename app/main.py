from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter

from app.database import create_tables
from app.graphql.schema import get_graphql_context, schema
from app.routes.categories import router as categories_router
from app.routes.expenses import router as expenses_router
from app.routes.summary import router as summary_router


STATIC_DIRECTORY = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    del application
    create_tables()
    yield


app = FastAPI(
    title="Expense Tracker API",
    version="0.1.0",
    lifespan=lifespan,
)

graphql_router = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
)

app.include_router(categories_router)
app.include_router(expenses_router)
app.include_router(summary_router)
app.include_router(graphql_router, prefix="/graphql")


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.mount(
    "/",
    StaticFiles(directory=STATIC_DIRECTORY, html=True),
    name="frontend",
)
