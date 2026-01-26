"""Scanner-specific exceptions."""

from __future__ import annotations


class ScannerError(Exception):
    """Base exception for scanner errors."""

    def __init__(self, message: str, scanner_type: str | None = None) -> None:
        self.message = message
        self.scanner_type = scanner_type
        super().__init__(self.message)


class ScannerValidationError(ScannerError):
    """Raised when scanner input validation fails."""


class ScannerExecutionError(ScannerError):
    """Raised when scanner execution fails."""

    def __init__(
        self,
        message: str,
        scanner_type: str | None = None,
        exit_code: int | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
    ) -> None:
        super().__init__(message, scanner_type)
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


class ScannerTimeoutError(ScannerError):
    """Raised when scanner execution times out."""


class ScannerParseError(ScannerError):
    """Raised when scanner output parsing fails."""

    def __init__(
        self,
        message: str,
        scanner_type: str | None = None,
        raw_output: str | None = None,
    ) -> None:
        super().__init__(message, scanner_type)
        self.raw_output = raw_output
