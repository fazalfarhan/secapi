"""Auth endpoints."""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.email import send_reset_email
from app.core.logging import get_logger
from app.core.security import generate_api_key, hash_api_key, verify_api_key
from app.db.models import ApiKeyResetToken, User
from app.db.session import get_db
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    ResetConfirm,
    ResetRequest,
    ResetResponse,
)

router = APIRouter()
logger = get_logger()


@router.post("/auth/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """Register a new user and generate an API key.

    The API key is only shown once - save it securely.
    """
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warning("Registration attempt with existing email", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    # Generate API key and hash it
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)

    # Create user
    user = User(
        email=request.email,
        api_key_hash=api_key_hash,
        tier="free",
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(
        "New user registered",
        user_id=str(user.id),
        email=request.email,
        tier="free",
    )

    # Return response with the plain API key (only shown once)
    return RegisterResponse(
        id=user.id,
        email=user.email,
        api_key=api_key,
        tier=user.tier,
        created_at=user.created_at,
    )


@router.post("/auth/reset-request", status_code=status.HTTP_202_ACCEPTED)
async def request_reset(
    request: ResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Request an API key reset.

    Generates a reset token and sends it via email (or console in dev).
    Always returns success to prevent email enumeration.
    """
    import secrets

    # Check if user exists
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    # Always return the same message regardless of whether user exists
    # This prevents email enumeration attacks
    if not user:
        logger.info("Reset requested for non-existent email", email=request.email)
        return {"message": "If the email exists, a reset link was sent"}

    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    token_hash = hash_api_key(reset_token)

    # Calculate expiry
    from datetime import datetime, timezone

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.RESET_TOKEN_EXPIRY_MINUTES
    )

    # Store reset token
    reset_record = ApiKeyResetToken(
        email=request.email,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(reset_record)
    await db.commit()

    logger.info(
        "Reset token generated",
        email=request.email,
        expires_at=expires_at.isoformat(),
    )

    # Send reset email
    try:
        send_reset_email(request.email, reset_token)
    except Exception as e:
        logger.error("Failed to send reset email", error=str(e))
        # Continue anyway - token is stored

    return {"message": "If the email exists, a reset link was sent"}


@router.post("/auth/reset-confirm", response_model=ResetResponse)
async def confirm_reset(
    request: ResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> ResetResponse:
    """Confirm API key reset with token from email.

    Validates the token and generates a new API key for the user.
    """
    from datetime import datetime, timezone

    # Find valid reset token
    result = await db.execute(
        select(ApiKeyResetToken).where(
            (ApiKeyResetToken.email == request.email)
            & (ApiKeyResetToken.used == False)  # noqa: E712
        )
    )
    reset_tokens = result.scalars().all()

    # Find matching token (compare hashes)
    valid_token = None
    for token in reset_tokens:
        if verify_api_key(request.token, token.token_hash):
            valid_token = token
            break

    if not valid_token:
        logger.warning("Invalid reset token provided", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check if token is expired
    if valid_token.expires_at < datetime.now(timezone.utc):
        logger.warning("Expired reset token provided", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    # Check if already used
    if valid_token.used:
        logger.warning("Already used reset token provided", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has already been used",
        )

    # Get user
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        logger.error("User not found for valid reset token", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Generate new API key
    new_api_key = generate_api_key()
    new_api_key_hash = hash_api_key(new_api_key)

    # Update user's API key
    user.api_key_hash = new_api_key_hash

    # Mark token as used
    valid_token.used = True

    await db.commit()

    logger.info(
        "API key reset successful",
        user_id=str(user.id),
        email=request.email,
    )

    return ResetResponse(
        api_key=new_api_key,
        message="API key regenerated successfully",
    )
