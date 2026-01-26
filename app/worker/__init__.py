"""Celery worker package."""

from app.worker.celery_app import celery_app
from app.worker.tasks import trivy_scan

__all__ = ["celery_app", "trivy_scan"]
