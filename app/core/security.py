"""Security utilities: API key generation and validation."""

from __future__ import annotations

import hashlib
import secrets

import bcrypt

from app.core.config import settings


def generate_api_key() -> str:
    """Generate a secure random API key.

    Note: bcrypt has a 72 byte limit, so we limit the key length.
    """
    # Use 24 bytes for token_urlsafe which produces ~32 characters
    # With prefix (7 chars) we're well under the 72 byte limit
    random_bytes = secrets.token_urlsafe(24)
    return f"{settings.API_KEY_PREFIX}{random_bytes}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key using bcrypt."""
    # bcrypt requires bytes
    api_key_bytes = api_key.encode("utf-8")
    # Ensure we don't exceed 72 bytes (bcrypt limit)
    if len(api_key_bytes) > 72:
        api_key_bytes = api_key_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(api_key_bytes, salt)
    return hashed.decode("utf-8")


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    api_key_bytes = api_key.encode("utf-8")
    if len(api_key_bytes) > 72:
        api_key_bytes = api_key_bytes[:72]
    hashed_bytes = hashed_key.encode("utf-8")
    return bcrypt.checkpw(api_key_bytes, hashed_bytes)
