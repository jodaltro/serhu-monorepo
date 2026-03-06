"""FastAPI application factory.

Creates and configures the SerHu API server that exposes the
Orchestrator's functionality to mobile and web clients.

Run with:
    uvicorn serhu_api.app:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
import logging.config
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from serhu_api.routes import health, beings
from serhu_api.config import Settings
from serhu_api.dependencies import clear_cache

# Configurar logging automaticamente (sempre ativo)
_logging_config_path = Path(__file__).parent.parent.parent.parent.parent / "logging.ini"
if _logging_config_path.exists():
    logging.config.fileConfig(_logging_config_path)
else:
    # Fallback: configuração básica se logging.ini não for encontrado
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager — startup and shutdown hooks."""
    logger.info("🚀 SerHu API starting up...")
    yield
    logger.info("🛑 SerHu API shutting down...")
    clear_cache()
    logger.info("✓ Cache cleared")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    logger.info("📝 Creating FastAPI application...")
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

    logger.info("📌 Registering routes...")
    app.include_router(health.router)
    app.include_router(beings.router)

    # CORS — origins configurable via CORS_ORIGINS env var.
    settings = Settings()
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    logger.info(f"🔓 CORS origins: {origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("✓ FastAPI application created successfully")
    return app


app = create_app()
