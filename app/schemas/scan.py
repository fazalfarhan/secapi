"""Scan-related schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SeverityCount(BaseModel):
    """Severity counts for scan results."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ScanMetadata(BaseModel):
    """Metadata for scan results."""

    scanned_at: str
    scanner_version: str
    scan_duration_seconds: float
    image: str | None = None


class VulnerabilityReference(BaseModel):
    """CVSS scores for a vulnerability."""

    score: float | None = None
    vector: str | None = None


class CVSSData(BaseModel):
    """CVSS scores from different sources."""

    vendor: VulnerabilityReference | None = None
    nvd: dict[str, float | str | None] | None = None


class Finding(BaseModel):
    """Single security finding."""

    id: str
    severity: str
    title: str
    description: str
    target: str
    package_name: str
    package_version: str
    fixed_version: str
    references: list[str]
    cvss: dict[str, Any] | None = None
    cwe_ids: list[str]
    primary_link: str


class ScanResults(BaseModel):
    """Normalized scan results."""

    scan_type: str
    status: str
    metadata: ScanMetadata
    summary: SeverityCount
    findings: list[Finding]


class ScanRequestOptions(BaseModel):
    """Options for Docker image scan."""

    severity: list[str] | None = Field(
        default=None,
        description="Severity levels to include (CRITICAL, HIGH, MEDIUM, LOW)",
    )
    scanners: list[str] | None = Field(
        default=None,
        description="Scanner types to enable (vuln, config, etc.)",
    )

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: list[str] | None) -> list[str] | None:
        """Validate severity levels."""
        if v is None:
            return None
        valid = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
        invalid = set(s.upper() for s in v) - valid
        if invalid:
            raise ValueError(f"Invalid severity levels: {invalid}")
        return [s.upper() for s in v]

    @field_validator("scanners")
    @classmethod
    def validate_scanners(cls, v: list[str] | None) -> list[str] | None:
        """Validate scanner types."""
        if v is None:
            return None
        valid = {"vuln", "config", "secret", "license"}
        invalid = set(s.lower() for s in v) - valid
        if invalid:
            raise ValueError(f"Invalid scanner types: {invalid}")
        return [s.lower() for s in v]


class DockerScanRequest(BaseModel):
    """Request to scan a Docker image."""

    image: str = Field(..., description="Docker image reference (e.g., nginx:latest)")
    options: ScanRequestOptions | None = Field(
        default=None,
        description="Scan options",
    )

    @field_validator("image")
    @classmethod
    def validate_image(cls, v: str) -> str:
        """Validate Docker image reference."""
        if not v or not v.strip():
            raise ValueError("Image cannot be empty")
        if len(v) > 500:
            raise ValueError("Image name too long")
        # Check for shell injection
        if any(char in v for char in ["$", ";", "&", "|", "`", "\n", "\r"]):
            raise ValueError("Invalid characters in image name")
        return v.strip()


class ScanSubmitResponse(BaseModel):
    """Response when submitting a scan."""

    scan_id: UUID
    status: str
    check_status_url: str
    created_at: datetime


class ScanStatusResponse(BaseModel):
    """Response when checking scan status."""

    scan_id: UUID
    status: str
    scan_type: str
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    results: ScanResults | None = None

    @field_validator("results", mode="before")
    @classmethod
    def validate_results(cls, v: dict[str, Any] | ScanResults | None) -> ScanResults | None:
        """Convert dict to ScanResults if needed."""
        if v is None:
            return None
        if isinstance(v, dict):
            return ScanResults(**v)
        return v


class ScanListResponse(BaseModel):
    """Response for listing scans."""

    total: int
    scans: list[ScanStatusResponse]
    page: int
    page_size: int
