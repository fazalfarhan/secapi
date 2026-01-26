"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    # Simple health check - no DB dependency for basic testing
    return {"status": "healthy", "database": "not_connected", "redis": "not_connected"}
