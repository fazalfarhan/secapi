"""Auth endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import generate_api_key, hash_api_key
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import RegisterRequest, RegisterResponse

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
    from sqlalchemy import select

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
