"""Celery tasks for security scanning."""

from __future__ import annotations

import json
import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import update
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


def _get_async_session():
    """Create a new async session for the current event loop."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,  # Disable echo in workers
        pool_pre_ping=True,
    )
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


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
    AsyncSessionLocal = _get_async_session()
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


@celery_app.task(bind=True, name="app.tasks.scan_tasks.execute_trivy_scan")
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
    scan_uuid = UUID(scan_id)

    async def _run(engine) -> dict:
        # Create session maker with this engine
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async def update_status(status: str, error_message: str | None = None, results: dict | None = None):
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
                    update(Scan).where(Scan.id == scan_id).values(**update_data)
                )
                await db.commit()

        try:
            await update_status("running")
            logger.info("Trivy scan started", scan_id=scan_id, image=image)

            scanner = TrivyScanner(timeout_seconds=300)
            input_data = {"image": image}
            if options:
                input_data["options"] = options

            results = scanner.scan(input_data)
            await update_status("completed", results=results)

            logger.info("Trivy scan completed", scan_id=scan_id, findings=len(results.get("findings", [])))
            return results

        except ScannerValidationError as e:
            await update_status("failed", error_message=f"Invalid input: {e.message}")
            raise
        except ScannerTimeoutError as e:
            await update_status("failed", error_message=f"Scan timed out: {e.message}")
            raise
        except ScannerExecutionError as e:
            await update_status("failed", error_message=f"Scan execution failed: {e.message}")
            raise
        except ScannerParseError as e:
            await update_status("failed", error_message=f"Failed to parse scan output: {e.message}")
            raise
        except ScannerError as e:
            await update_status("failed", error_message=f"Scan error: {e.message}")
            raise
        except Exception as e:
            await update_status("failed", error_message=f"Unexpected error: {str(e)}")
            raise

    async def _run_with_engine():
        # Create engine inside the event loop
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
        )
        try:
            return await _run(engine)
        finally:
            await engine.dispose()

    # Create new loop and close it properly
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_run_with_engine())
    finally:
        # Close the loop to clean up resources
        loop.close()
