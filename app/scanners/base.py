"""Base scanner interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


class BaseScanner(ABC):
    """Abstract base class for security scanners."""

    scanner_type: str
    scanner_version: str | None = None

    @abstractmethod
    async def scan(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute scan and return normalized results.

        Args:
            input_data: Scan input parameters (image, file path, etc.)

        Returns:
            Normalized scan results in unified format

        Raises:
            ScannerValidationError: If input validation fails
            ScannerExecutionError: If scan execution fails
            ScannerTimeoutError: If scan times out
            ScannerParseError: If output parsing fails
        """
        ...

    @abstractmethod
    def validate_input(self, input_data: dict[str, Any]) -> bool:
        """Validate input parameters before scanning.

        Args:
            input_data: Input parameters to validate

        Returns:
            True if valid

        Raises:
            ScannerValidationError: If validation fails
        """
        ...

    @staticmethod
    def normalize_severity(severity: str) -> str:
        """Normalize severity levels across scanners.

        Args:
            severity: Original severity string

        Returns:
            Normalized severity: CRITICAL, HIGH, MEDIUM, LOW, or INFO
        """
        severity_map = {
            "CRITICAL": "CRITICAL",
            "CRITICAL": "CRITICAL",
            "HIGH": "HIGH",
            "HIGH": "HIGH",
            "MEDIUM": "MEDIUM",
            "MEDIUM": "MEDIUM",
            "MODERATE": "MEDIUM",
            "LOW": "LOW",
            "LOW": "LOW",
            "INFO": "INFO",
            "INFO": "INFO",
            "UNKNOWN": "INFO",
        }
        return severity_map.get(severity.upper(), "INFO")

    @staticmethod
    def create_scan_result(
        scan_type: str,
        scanner_version: str,
        findings: list[dict[str, Any]],
        scan_duration: float,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create unified scan result format.

        Args:
            scan_type: Type of scan performed
            scanner_version: Scanner version string
            findings: List of vulnerability/security findings
            scan_duration: Scan duration in seconds
            metadata: Additional metadata to include

        Returns:
            Unified scan result dictionary
        """
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for finding in findings:
            severity = finding.get("severity", "INFO").upper()
            if severity in summary:
                summary[severity] += 1

        result: dict[str, Any] = {
            "scan_type": scan_type,
            "status": "completed",
            "metadata": {
                "scanned_at": datetime.now(UTC).isoformat(),
                "scanner_version": scanner_version,
                "scan_duration_seconds": round(scan_duration, 2),
            },
            "summary": summary,
            "findings": findings,
        }

        if metadata:
            result["metadata"].update(metadata)

        return result
