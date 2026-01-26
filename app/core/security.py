"""Security utilities: API key generation and validation."""

import secrets

import passlib.hash

from app.core.config import settings


def generate_api_key() -> str:
    """Generate a secure random API key."""
    random_bytes = secrets.token_urlsafe(settings.API_KEY_LENGTH)
    return f"{settings.API_KEY_PREFIX}{random_bytes}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key using bcrypt."""
    return passlib.hash.bcrypt.hash(api_key)


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return passlib.hash.bcrypt.verify(api_key, hashed_key)
