"""Celery tasks for security scanning."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from celery import Task
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.celery import celery_app
from app.core.config import settings
from app.db.models import Scan
from app.scanners.exceptions import (
    ScannerError,
    ScannerExecutionError,
    ScannerParseError,
    ScannerTimeoutError,
    ScannerValidationError,
)
from app.scanners.trivy import TrivyScanner
from structlog import get_logger

logger = get_logger()

# Create async engine for worker
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class DatabaseTask(Task):
    """Base task with database session management."""

    _db: AsyncSession | None = None

    @property
    def db(self) -> AsyncSession:
        """Get or create database session."""
        if self._db is None:
            self._db = AsyncSessionLocal()
        return self._db

    async def cleanup_db(self) -> None:
        """Close database session."""
        if self._db is not None:
            await self._db.close()
            self._db = None

    def after_return(self, *args: object, **kwargs: object) -> None:
        """Cleanup after task completion."""
        # Run cleanup synchronously by creating new event loop if needed
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Loop is running, schedule cleanup
                loop.create_task(self.cleanup_db())
            else:
                loop.run_until_complete(self.cleanup_db())
        except RuntimeError:
            # No loop, create new one
            asyncio.run(self.cleanup_db())


async def update_scan_status(
    scan_id: UUID,
    status: str,
    error_message: str | None = None,
    results: dict | None = None,
) -> None:
    """Update scan status in database.

    Args:
        scan_id: Scan UUID
        status: New status (pending, running, completed, failed)
        error_message: Error message if failed
        results: Scan results if completed
    """
    async with AsyncSessionLocal() as db:
        update_data: dict = {"status": status}

        if status == "running":
            update_data["started_at"] = datetime.now(UTC)
        elif status in ("completed", "failed"):
            update_data["completed_at"] = datetime.now(UTC)

        if error_message:
            update_data["error_message"] = error_message

        if results:
            update_data["results"] = json.dumps(results)

        await db.execute(
            update(Scan)
            .where(Scan.id == scan_id)
            .values(**update_data)
        )
        await db.commit()


@celery_app.task(base=DatabaseTask, bind=True, name="app.tasks.scan_tasks.execute_trivy_scan")
def execute_trivy_scan(self, scan_id: str, image: str, options: dict | None = None) -> dict:
    """Execute Trivy scan asynchronously.

    Args:
        self: Celery task instance
        scan_id: Scan UUID as string
        image: Docker image to scan
        options: Optional scan options

    Returns:
        Scan results dictionary

    Raises:
        Exception: If scan fails after retries
    """
    import asyncio

    async def _run_scan() -> dict:
        scan_uuid = UUID(scan_id)

        try:
            # Update status to running
            await update_scan_status(scan_uuid, "running")
            logger.info("Trivy scan started", scan_id=scan_id, image=image)

            # Initialize scanner
            scanner = TrivyScanner(timeout_seconds=300)

            # Execute scan
            input_data = {"image": image}
            if options:
                input_data["options"] = options

            results = await scanner.scan(input_data)

            # Update with results
            await update_scan_status(scan_uuid, "completed", results=results)

            logger.info("Trivy scan completed", scan_id=scan_id, findings=len(results.get("findings", [])))

            return results

        except ScannerValidationError as e:
            error_msg = f"Invalid input: {e.message}"
            await update_scan_status(scan_uuid, "failed", error_message=error_msg)
            logger.error("Trivy scan validation failed", scan_id=scan_id, error=error_msg)
            raise

        except ScannerTimeoutError as e:
            error_msg = f"Scan timed out: {e.message}"
            await update_scan_status(scan_uuid, "failed", error_message=error_msg)
            logger.error("Trivy scan timed out", scan_id=scan_id)
            raise

        except ScannerExecutionError as e:
            error_msg = f"Scan execution failed: {e.message}"
            await update_scan_status(scan_uuid, "failed", error_message=error_msg)
            logger.error("Trivy scan execution failed", scan_id=scan_id, error=error_msg)
            raise

        except ScannerParseError as e:
            error_msg = f"Failed to parse scan output: {e.message}"
            await update_scan_status(scan_uuid, "failed", error_message=error_msg)
            logger.error("Trivy scan parse failed", scan_id=scan_id, error=error_msg)
            raise

        except ScannerError as e:
            error_msg = f"Scan error: {e.message}"
            await update_scan_status(scan_uuid, "failed", error_message=error_msg)
            logger.error("Trivy scan error", scan_id=scan_id, error=error_msg)
            raise

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            await update_scan_status(scan_uuid, "failed", error_message=error_msg)
            logger.error("Unexpected error in Trivy scan", scan_id=scan_id, error=str(e))
            raise

    # Use asyncio.run() with proper cleanup
    # This creates a new event loop for each task execution
    return asyncio.run(_run_scan())


@celery_app.task(name="app.tasks.scan_tasks.execute_checkov_scan")
def execute_checkov_scan(scan_id: str, target: str, options: dict | None = None) -> dict:
    """Execute Checkov scan asynchronously.

    Args:
        scan_id: Scan UUID as string
        target: Target to scan (file path, repo URL, etc.)
        options: Optional scan options

    Returns:
        Scan results dictionary
    """
    # TODO: Implement in Phase 1-2
    raise NotImplementedError("Checkov scanner not yet implemented")


@celery_app.task(name="app.tasks.scan_tasks.execute_trufflehog_scan")
def execute_trufflehog_scan(scan_id: str, target: str, options: dict | None = None) -> dict:
    """Execute TruffleHog scan asynchronously.

    Args:
        scan_id: Scan UUID as string
        target: Target to scan (file path, repo URL, etc.)
        options: Optional scan options

    Returns:
        Scan results dictionary
    """
    # TODO: Implement in Phase 1-3
    raise NotImplementedError("TruffleHog scanner not yet implemented")
