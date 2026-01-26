"""Celery worker configuration and tasks for security scanning."""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "secapi",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes for long-running scans
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


@celery_app.task(name="health_check")
def health_check() -> str:
    """Simple health check task."""
    return "OK"
