"""Tests for scan API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.schemas.scan import DockerScanRequest, ScanSubmitResponse


@pytest.mark.asyncio
class TestSubmitDockerScan:
    """Tests for POST /api/v1/scan/docker endpoint."""

    async def test_submit_scan_success(
        self,
        async_client,
        test_api_key: str,
    ) -> None:
        """Test successful scan submission."""
        response = await async_client.post(
            "/api/v1/scan/docker",
            json={"image": "nginx:latest"},
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 202
        data = response.json()

        assert "scan_id" in data
        assert data["status"] == "queued"
        assert "/api/v1/scans/" in data["check_status_url"]
        assert "created_at" in data

    async def test_submit_scan_with_options(
        self,
        async_client,
        test_api_key: str,
    ) -> None:
        """Test scan submission with custom options."""
        response = await async_client.post(
            "/api/v1/scan/docker",
            json={
                "image": "python:3.11",
                "options": {
                    "severity": ["CRITICAL", "HIGH"],
                    "scanners": ["vuln"],
                },
            },
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 202
        data = response.json()
        assert "scan_id" in data

    async def test_submit_scan_missing_auth(
        self,
        async_client,
    ) -> None:
        """Test scan submission fails without authentication."""
        response = await async_client.post(
            "/api/v1/scan/docker",
            json={"image": "nginx:latest"},
        )

        assert response.status_code == 401

    async def test_submit_scan_invalid_auth(
        self,
        async_client,
    ) -> None:
        """Test scan submission fails with invalid API key."""
        response = await async_client.post(
            "/api/v1/scan/docker",
            json={"image": "nginx:latest"},
            headers={"Authorization": "Bearer invalid_key"},
        )

        assert response.status_code == 401

    async def test_submit_scan_invalid_image(
        self,
        async_client,
        test_api_key: str,
    ) -> None:
        """Test scan submission fails with invalid image."""
        response = await async_client.post(
            "/api/v1/scan/docker",
            json={"image": "invalid;format"},
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 422  # Validation error

    async def test_submit_scan_empty_image(
        self,
        async_client,
        test_api_key: str,
    ) -> None:
        """Test scan submission fails with empty image."""
        response = await async_client.post(
            "/api/v1/scan/docker",
            json={"image": ""},
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 422

    async def test_submit_scan_shell_injection(
        self,
        async_client,
        test_api_key: str,
    ) -> None:
        """Test scan submission blocks shell injection."""
        response = await async_client.post(
            "/api/v1/scan/docker",
            json={"image": "nginx; cat /etc/passwd"},
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 422


@pytest.mark.asyncio
class TestGetScanStatus:
    """Tests for GET /api/v1/scans/{scan_id} endpoint."""

    async def test_get_scan_pending(
        self,
        async_client,
        test_api_key: str,
        db_session,
    ) -> None:
        """Test getting status of pending scan."""
        # First submit a scan
        submit_response = await async_client.post(
            "/api/v1/scan/docker",
            json={"image": "nginx:latest"},
            headers={"Authorization": f"Bearer {test_api_key}"},
        )
        scan_id = submit_response.json()["scan_id"]

        # Get status
        response = await async_client.get(
            f"/api/v1/scans/{scan_id}",
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["scan_id"] == scan_id
        assert data["status"] in ("queued", "running", "pending")
        assert "created_at" in data

    async def test_get_scan_not_found(
        self,
        async_client,
        test_api_key: str,
    ) -> None:
        """Test getting status of non-existent scan."""
        fake_id = uuid4()
        response = await async_client.get(
            f"/api/v1/scans/{fake_id}",
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 404

    async def test_get_scan_unauthorized(
        self,
        async_client,
        test_api_key: str,
        db_session,
    ) -> None:
        """Test getting status without authentication."""
        # First submit a scan
        submit_response = await async_client.post(
            "/api/v1/scan/docker",
            json={"image": "nginx:latest"},
            headers={"Authorization": f"Bearer {test_api_key}"},
        )
        scan_id = submit_response.json()["scan_id"]

        # Try without auth
        response = await async_client.get(f"/api/v1/scans/{scan_id}")

        assert response.status_code == 401


@pytest.mark.asyncio
class TestListScans:
    """Tests for GET /api/v1/scans endpoint."""

    async def test_list_scans_empty(
        self,
        async_client,
        test_api_key: str,
    ) -> None:
        """Test listing scans when user has none."""
        response = await async_client.get(
            "/api/v1/scans",
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "scans" in data
        assert data["total"] == 0
        assert len(data["scans"]) == 0

    async def test_list_scans_with_scans(
        self,
        async_client,
        test_api_key: str,
    ) -> None:
        """Test listing scans after submitting some."""
        # Submit a scan
        await async_client.post(
            "/api/v1/scan/docker",
            json={"image": "nginx:latest"},
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        # List scans
        response = await async_client.get(
            "/api/v1/scans",
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        assert len(data["scans"]) >= 1

    async def test_list_scans_pagination(
        self,
        async_client,
        test_api_key: str,
    ) -> None:
        """Test listing scans with pagination."""
        response = await async_client.get(
            "/api/v1/scans?page=1&page_size=10",
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 10

    async def test_list_scans_filter_by_status(
        self,
        async_client,
        test_api_key: str,
    ) -> None:
        """Test listing scans filtered by status."""
        response = await async_client.get(
            "/api/v1/scans?status=completed",
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 200
