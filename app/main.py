"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Open-source security scanning API platform",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
        }

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "database": "not_connected", "redis": "not_connected"}

    return app


app = create_app()
