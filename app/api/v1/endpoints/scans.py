"""Scan endpoints."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.logging import get_logger
from app.db.models import Scan, User
from app.db.session import get_db
from app.schemas.scan import (
    DockerScanRequest,
    ScanListResponse,
    ScanStatusResponse,
    ScanSubmitResponse,
)
from app.tasks.scan_tasks import execute_trivy_scan

router = APIRouter()
logger = get_logger()


@router.post("/scan/docker", response_model=ScanSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_docker_scan(
    request: DockerScanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScanSubmitResponse:
    """Submit a Docker image vulnerability scan.

    Queues a Trivy scan for the specified Docker image and returns immediately.
    Use the returned scan_id to check scan status and results.
    """
    scan_id = uuid4()

    # Create scan record in database
    input_data = {
        "image": request.image,
        "options": request.options.model_dump(exclude_none=True) if request.options else None,
    }

    scan = Scan(
        id=scan_id,
        user_id=current_user.id,
        scan_type="trivy",
        status="pending",
        input_data=json.dumps(input_data),
    )

    db.add(scan)
    await db.commit()

    # Queue Celery task
    execute_trivy_scan.delay(
        scan_id=str(scan_id),
        image=request.image,
        options=request.options.model_dump(exclude_none=True) if request.options else None,
    )

    logger.info(
        "Docker scan submitted",
        scan_id=str(scan_id),
        user_id=str(current_user.id),
        image=request.image,
    )

    return ScanSubmitResponse(
        scan_id=scan_id,
        status="queued",
        check_status_url=f"/api/v1/scans/{scan_id}",
        created_at=datetime.now(UTC),
    )


@router.get("/scans/{scan_id}", response_model=ScanStatusResponse)
async def get_scan_status(
    scan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScanStatusResponse:
    """Get scan status and results.

    Returns the current status of a scan. If the scan is complete,
    includes the full results.
    """
    result = await db.execute(
        select(Scan).where(
            Scan.id == scan_id,
            Scan.user_id == current_user.id,
        )
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    # Parse results if available
    results_data = None
    if scan.results:
        try:
            results_data = json.loads(scan.results) if isinstance(scan.results, str) else scan.results
        except json.JSONDecodeError:
            logger.error("Failed to parse scan results", scan_id=str(scan_id))

    return ScanStatusResponse(
        scan_id=scan.id,
        status=scan.status,
        scan_type=scan.scan_type,
        created_at=scan.created_at,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        results=results_data,
    )


@router.get("/scans", response_model=ScanListResponse)
async def list_scans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    scan_type: str | None = Query(None, alias="type"),
) -> ScanListResponse:
    """List all scans for the authenticated user.

    Supports pagination and filtering by status and scan type.
    """
    query = select(Scan).where(Scan.user_id == current_user.id)

    if status_filter:
        query = query.where(Scan.status == status_filter)

    if scan_type:
        query = query.where(Scan.scan_type == scan_type)

    # Order by created_at descending
    query = query.order_by(Scan.created_at.desc())

    # Get total count
    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    scans = result.scalars().all()

    scan_responses = []
    for scan in scans:
        results_data = None
        if scan.results:
            try:
                results_data = json.loads(scan.results) if isinstance(scan.results, str) else scan.results
            except json.JSONDecodeError:
                pass

        scan_responses.append(ScanStatusResponse(
            scan_id=scan.id,
            status=scan.status,
            scan_type=scan.scan_type,
            created_at=scan.created_at,
            started_at=scan.started_at,
            completed_at=scan.completed_at,
            error_message=scan.error_message,
            results=results_data,
        ))

    return ScanListResponse(
        total=total,
        scans=scan_responses,
        page=page,
        page_size=page_size,
    )


@router.delete("/scans/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Delete a scan record.

    Only completed or failed scans can be deleted.
    """
    result = await db.execute(
        select(Scan).where(
            Scan.id == scan_id,
            Scan.user_id == current_user.id,
        )
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    if scan.status in ("pending", "running"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete scan in progress",
        )

    await db.delete(scan)
    await db.commit()

    logger.info("Scan deleted", scan_id=str(scan_id), user_id=str(current_user.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
