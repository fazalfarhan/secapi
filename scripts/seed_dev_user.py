#!/usr/bin/env python3
"""Seed script to create a dev user for testing.

Run with:
    python scripts/seed_dev_user.py

Or via docker:
    docker-compose exec api python scripts/seed_dev_user.py
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path for imports
sys.path.insert(0, "/Users/ff/sultans/secapi")

from app.core.security import generate_api_key, hash_api_key
from app.db.base import Base
from app.db.models import User
from app.db.session import AsyncSessionLocal


DEV_EMAIL = "dev@secapi.test"


async def create_dev_user() -> None:
    """Create a dev user if it doesn't exist."""
    async with AsyncSessionLocal() as db:
        # Check if dev user already exists
        result = await db.execute(select(User).where(User.email == DEV_EMAIL))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # Generate new API key for existing user
            api_key = generate_api_key()
            api_key_hash = hash_api_key(api_key)
            existing_user.api_key_hash = api_key_hash
            await db.commit()
            await db.refresh(existing_user)
            print(f"Dev user already exists. Reset API key:\n")
            print(f"  Email: {DEV_EMAIL}")
            print(f"  User ID: {existing_user.id}")
            print(f"  API Key: {api_key}")
            return

        # Create new dev user
        api_key = generate_api_key()
        api_key_hash = hash_api_key(api_key)

        user = User(
            email=DEV_EMAIL,
            api_key_hash=api_key_hash,
            tier="free",
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        print("Dev user created:\n")
        print(f"  Email: {DEV_EMAIL}")
        print(f"  User ID: {user.id}")
        print(f"  API Key: {api_key}")
        print("\nUse this API key for testing:")
        print(f"  curl -H 'X-API-Key: {api_key}' http://localhost:8000/api/v1/health")


if __name__ == "__main__":
    try:
        asyncio.run(create_dev_user())
    except Exception as e:
        print(f"Error creating dev user: {e}", file=sys.stderr)
        sys.exit(1)
