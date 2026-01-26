"""Security scanners package."""

from __future__ import annotations

from app.scanners.base import BaseScanner
from app.scanners.trivy import TrivyScanner

__all__ = ["BaseScanner", "TrivyScanner"]
