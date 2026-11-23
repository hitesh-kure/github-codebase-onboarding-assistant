from contextlib import asynccontextmanager

from app.api.repositories import router as repositories_router

from fastapi import FastAPI

from app.core.database import engine, Base
from app.models.repository import Repository


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(
    title="GitHub Codebase Onboarding Assistant",
    description="Ask questions about GitHub repositories",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(repositories_router)

@app.get("/")
async def home():
    return {
        "message": "GitHub Codebase Onboarding Assistant API is running!"
    }