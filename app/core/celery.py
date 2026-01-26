"""Celery application factory."""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "secapi",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.scan_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=300,  # 5 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Configure retry settings
celery_app.conf.task_aut_retry_for = (Exception,)
celery_app.conf.task_retry_kwargs = {"max_retries": 3, "countdown": 60}
celery_app.conf.task_retry_backoff = True
celery_app.conf.task_retry_backoff_max = 600  # 10 minutes
