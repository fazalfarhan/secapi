"""Common Pydantic schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str
    redis: str


class APIErrorResponse(BaseModel):
    """API error response."""

    detail: str = Field(..., description="Error message")
