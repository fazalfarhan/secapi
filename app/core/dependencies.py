"""FastAPI dependencies."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_api_key
from app.db.session import get_db
from app.db.models import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get authenticated user from API key."""
    api_key = credentials.credentials

    # Get all users and verify API key (since we can't query by hash directly)
    result = await db.execute(select(User))
    users = result.scalars().all()

    for user in users:
        if verify_api_key(api_key, user.api_key_hash):
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
    )
