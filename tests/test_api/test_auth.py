"""Tests for auth API endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
class TestRegister:
    """Tests for POST /api/v1/auth/register endpoint."""

    async def test_register_success(self, async_client) -> None:
        """Test successful user registration."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "newuser@example.com"},
        )

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["email"] == "newuser@example.com"
        assert "api_key" in data
        assert data["api_key"].startswith("secapi_")
        assert data["tier"] == "free"
        assert "created_at" in data

    async def test_register_duplicate_email(self, async_client, test_api_key: str) -> None:
        """Test registration fails with duplicate email."""
        # First registration
        await async_client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com"},
        )

        # Second registration with same email
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "duplicate@example.com"},
        )

        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()

    async def test_register_invalid_email(self, async_client) -> None:
        """Test registration fails with invalid email."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email"},
        )

        assert response.status_code == 422

    async def test_register_missing_email(self, async_client) -> None:
        """Test registration fails with missing email."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={},
        )

        assert response.status_code == 422

    async def test_register_empty_email(self, async_client) -> None:
        """Test registration fails with empty email."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": ""},
        )

        assert response.status_code == 422

    async def test_register_creates_unique_api_key(self, async_client) -> None:
        """Test that each registration creates a unique API key."""
        response1 = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "user1@example.com"},
        )
        response2 = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "user2@example.com"},
        )

        assert response1.status_code == 201
        assert response2.status_code == 201

        api_key_1 = response1.json()["api_key"]
        api_key_2 = response2.json()["api_key"]

        assert api_key_1 != api_key_2

    async def test_register_api_key_format(self, async_client) -> None:
        """Test that generated API key has correct format."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "format-test@example.com"},
        )

        assert response.status_code == 201
        data = response.json()

        api_key = data["api_key"]
        assert api_key.startswith("secapi_")
        # secapi_ (7 chars) + token_urlsafe(24) (32 chars) ≈ 39 chars
        assert len(api_key) >= 30
