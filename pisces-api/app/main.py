"""FastAPI application entry point for Pisces API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.core.database import create_all_tables  # noqa: E402
from app.core.logging import setup_logging  # noqa: E402
from app.routers import (  # noqa: E402
    chapter_router,
    glossary_router,
    novel_router,
    translation_router,
)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all DB tables on startup (Alembic handles upgrades in production)."""
    await create_all_tables()
    yield


app = FastAPI(
    title="Pisces API",
    description="Pisces",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(novel_router)
app.include_router(chapter_router)
app.include_router(translation_router)
app.include_router(glossary_router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "pisces-api"}
