"""User Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: str = Field(..., description="User email address")


class UserCreate(UserBase):
    """User creation schema."""

    api_key: str = Field(..., description="API key for authentication")


class UserResponse(UserBase):
    """User response schema."""

    id: UUID = Field(..., description="User ID")
    tier: str = Field(..., description="User tier (free, pro, enterprise)")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic config."""

        from_attributes = True
