"""FastAPI application factory.

Creates and configures the SerHu API server that exposes the
Orchestrator's functionality to mobile and web clients.

Run with:
    uvicorn serhu_api.app:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from serhu_api.routes import health, beings
from serhu_api.config import Settings
from serhu_api.dependencies import clear_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager — startup and shutdown hooks."""
    yield
    clear_cache()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="SerHu API",
        description=(
            "REST API for the SerHu synthetic Being platform. "
            "Exposes the Orchestrator for Being lifecycle management, "
            "chat, sleep cycles, memory retrieval, and visual morphogenesis."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(beings.router)

    # CORS — origins configurable via CORS_ORIGINS env var.
    settings = Settings()
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()
