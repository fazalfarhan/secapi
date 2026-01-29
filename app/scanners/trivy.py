"""Trivy scanner implementation for Docker image vulnerability scanning."""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import time
from typing import Any

from structlog import get_logger

from app.scanners.base import BaseScanner
from app.scanners.exceptions import (
    ScannerExecutionError,
    ScannerParseError,
    ScannerTimeoutError,
    ScannerValidationError,
)

logger = get_logger()

# Docker image reference regex (simplified)
IMAGE_RE = re.compile(
    r"^(?P<host>[a-z0-9.-]+(:[0-9]+)?/)?"
    r"(?P<namespace>[a-z0-9_]+/)?"
    r"(?P<name>[a-z0-9_-]+)"
    r"(?::(?P<tag>[\w.-]+))?"
    r"(?:@(?P<digest>[a-z0-9_]+:[a-f0-9]+))?$",
    re.IGNORECASE,
)

# Whitelist of allowed Docker registries
ALLOWED_REGISTRIES = {
    "docker.io",
    "registry-1.docker.io",
    "ghcr.io",
    "gcr.io",
    "quay.io",
    "public.ecr.aws",
    "mcr.microsoft.com",
    "",
}


class TrivyScanner(BaseScanner):
    """Trivy scanner for Docker image vulnerability scanning."""

    scanner_type = "trivy"
    scanner_version = "0.55.0"  # Default version, will be detected at runtime

    def __init__(self, timeout_seconds: int = 300) -> None:
        """Initialize Trivy scanner.

        Args:
            timeout_seconds: Maximum time to wait for scan completion
        """
        self.timeout_seconds = timeout_seconds
        self._detected_version: str | None = None

    def scan(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Execute Trivy scan on Docker image.

        Args:
            input_data: Must contain 'image' key with Docker image reference.
                Optional 'options' dict with:
                - severity: list of severity levels (default: all)
                - scanners: list of scanner types (default: ["vuln"])

        Returns:
            Normalized scan results

        Raises:
            ScannerValidationError: If input validation fails
            ScannerExecutionError: If scan execution fails
            ScannerTimeoutError: If scan times out
            ScannerParseError: If output parsing fails
        """
        self.validate_input(input_data)

        image = input_data["image"]
        options = input_data.get("options", {})
        severity = options.get("severity", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        scanners = options.get("scanners", ["vuln"])

        logger.info(
            "Starting Trivy scan",
            image=image,
            severity=severity,
            scanners=scanners,
        )

        start_time = time.time()

        try:
            raw_output = self._execute_trivy(image, severity, scanners)
            scan_duration = time.time() - start_time

            parsed = self._parse_trivy_output(raw_output)
            findings = self._normalize_findings(parsed.get("Results", []))
            metadata = {
                "image": image,
                "trivy_version": self._detected_version or self.scanner_version,
            }

            result = self.create_scan_result(
                scan_type="docker",
                scanner_version=f"trivy-{self._detected_version or self.scanner_version}",
                findings=findings,
                scan_duration=scan_duration,
                metadata=metadata,
            )

            logger.info(
                "Trivy scan completed",
                image=image,
                duration=scan_duration,
                findings_count=len(findings),
            )

            return result

        except subprocess.TimeoutExpired as e:
            logger.error("Trivy scan timed out", image=image, timeout=self.timeout_seconds)
            raise ScannerTimeoutError(
                f"Scan timed out after {self.timeout_seconds} seconds",
                scanner_type=self.scanner_type,
            ) from e
        except subprocess.CalledProcessError as e:
            logger.error(
                "Trivy scan failed",
                image=image,
                exit_code=e.returncode,
                stderr=e.stderr if e.stderr else "",
            )
            raise ScannerExecutionError(
                f"Scan failed with exit code {e.returncode}",
                scanner_type=self.scanner_type,
                exit_code=e.returncode,
                stdout=e.stdout if e.stdout else None,
                stderr=e.stderr if e.stderr else None,
            ) from e
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Trivy JSON output", error=str(e))
            raise ScannerParseError(
                f"Failed to parse scanner output: {e}",
                scanner_type=self.scanner_type,
                raw_output=str(e),
            ) from e

    def validate_input(self, input_data: dict[str, Any]) -> bool:
        """Validate Docker image reference.

        Args:
            input_data: Must contain 'image' key

        Returns:
            True if valid

        Raises:
            ScannerValidationError: If validation fails
        """
        if not isinstance(input_data, dict):
            raise ScannerValidationError("Input must be a dictionary")

        if "image" not in input_data:
            raise ScannerValidationError("Missing required field: 'image'")

        image = input_data["image"]

        if not isinstance(image, str):
            raise ScannerValidationError("'image' must be a string")

        image = image.strip()

        if not image or len(image) > 500:
            raise ScannerValidationError("Invalid image name")

        # Check for shell injection attempts
        if any(char in image for char in ["$", ";", "&", "|", "`", "\n", "\r"]):
            raise ScannerValidationError("Invalid characters in image name")

        # Validate Docker image format
        match = IMAGE_RE.match(image)
        if not match:
            raise ScannerValidationError(f"Invalid Docker image format: {image}")

        # Check registry is allowed (if specified)
        host = match.group("host") or ""
        if host and host.rstrip("/") not in ALLOWED_REGISTRIES:
            raise ScannerValidationError(f"Registry not allowed: {host}")

        return True

    def _execute_trivy(
        self,
        image: str,
        severity: list[str],
        scanners: list[str],
    ) -> str:
        """Execute Trivy command and return JSON output.

        Args:
            image: Docker image reference
            severity: List of severity levels
            scanners: List of scanner types

        Returns:
            Raw JSON output from Trivy

        Raises:
            subprocess.TimeoutExpired: If command times out
            subprocess.CalledProcessError: If command fails
        """
        severity_str = ",".join(s.upper() for s in severity)
        scanners_str = ",".join(s.lower() for s in scanners)

        # Build Trivy command
        # Using Docker to run Trivy for isolation
        cmd = [
            "trivy",
            "image",
            "--format",
            "json",
            "--quiet",
            "--severity",
            severity_str,
            "--scanners",
            scanners_str,
            "--no-progress",
            image,
        ]

        logger.debug("Executing Trivy command", command=" ".join(shlex.quote(c) for c in cmd))

        # Run subprocess (synchronous - Celery already handles async)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )

        if result.returncode != 0:
            result.check_returncode()

        # Try to detect version from output
        if result.stderr:
            version_match = re.search(r"version:\s*(\d+\.\d+\.\d+)", result.stderr)
            if version_match:
                self._detected_version = version_match.group(1)

        return result.stdout

    def _parse_trivy_output(self, raw_output: str) -> dict[str, Any]:
        """Parse Trivy JSON output.

        Args:
            raw_output: Raw JSON string from Trivy

        Returns:
            Parsed Trivy results dictionary

        Raises:
            ScannerParseError: If JSON parsing fails
        """
        try:
            data = json.loads(raw_output)

            if isinstance(data, list):
                return {"Results": data}
            if isinstance(data, dict):
                return data

            raise ScannerParseError("Unexpected output format from Trivy")

        except json.JSONDecodeError as e:
            raise ScannerParseError(
                f"Failed to parse Trivy JSON output: {e}",
                raw_output=raw_output[:500],
            ) from e

    def _normalize_findings(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert Trivy results to unified finding format.

        Args:
            results: Trivy Results list

        Returns:
            List of normalized findings
        """
        findings = []

        for result in results:
            target = result.get("Target", "")
            vulnerabilities = result.get("Vulnerabilities", [])

            for vuln in vulnerabilities:
                finding = {
                    "id": vuln.get("VulnerabilityID", ""),
                    "severity": self.normalize_severity(vuln.get("Severity", "UNKNOWN")),
                    "title": vuln.get("Title", ""),
                    "description": vuln.get("Description", ""),
                    "target": target,
                    "package_name": vuln.get("PkgName", ""),
                    "package_version": vuln.get("InstalledVersion", ""),
                    "fixed_version": vuln.get("FixedVersion", ""),
                    "references": vuln.get("References", []),
                    "cvss": self._extract_cvss(vuln),
                    "cwe_ids": vuln.get("CWEIDs", []),
                    "primary_link": vuln.get("PrimaryURL", ""),
                }
                findings.append(finding)

        return findings

    @staticmethod
    def _extract_cvss(vuln: dict[str, Any]) -> dict[str, Any]:
        """Extract CVSS scores from vulnerability data.

        Args:
            vuln: Vulnerability dictionary from Trivy

        Returns:
            CVSS scores dict with vendor, v2, and v3 scores
        """
        cvss: dict[str, Any] = {}

        if cvss_data := vuln.get("CVSS"):
            # Vendor specific scores
            if vendor := cvss_data.get("vendor"):
                cvss["vendor"] = {
                    "score": vendor.get("Score"),
                    "vector": vendor.get("V3Vector") or vendor.get("V2Vector"),
                }

            # NVD scores
            if nvd := cvss_data.get("nvd"):
                cvss["nvd"] = {
                    "v2_score": nvd.get("V2Score"),
                    "v2_vector": nvd.get("V2Vector"),
                    "v3_score": nvd.get("V3Score"),
                    "v3_vector": nvd.get("V3Vector"),
                }

        return cvss


# Import asyncio at module level for to_thread
import asyncio
