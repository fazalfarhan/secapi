"""Auth Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr = Field(..., description="User email address")


class RegisterResponse(BaseModel):
    """User registration response schema."""

    id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    api_key: str = Field(..., description="Generated API key (only shown once)")
    tier: str = Field(..., description="User tier (free, pro, enterprise)")
    created_at: datetime = Field(..., description="Account creation timestamp")

    model_config = {"from_attributes": True}


class ResetRequest(BaseModel):
    """API key reset request schema."""

    email: EmailStr = Field(..., description="Email address for the account")


class ResetConfirm(BaseModel):
    """API key reset confirmation schema."""

    email: EmailStr = Field(..., description="Email address for the account")
    token: str = Field(..., min_length=1, description="Reset token from email")


class ResetResponse(BaseModel):
    """API key reset response schema."""

    api_key: str = Field(..., description="Newly generated API key (save it securely)")
    message: str = Field(..., description="Success message")
