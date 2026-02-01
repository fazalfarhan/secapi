"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

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

    @app.get("/", response_class=HTMLResponse)
    async def root() -> HTMLResponse:
        """Render landing page."""
        from pathlib import Path

        html_path = Path(__file__).parent / "templates" / "index.html"
        return HTMLResponse(content=html_path.read_text())

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "database": "not_connected", "redis": "not_connected"}

    return app


app = create_app()
