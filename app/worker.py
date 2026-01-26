"""Celery worker entry point."""

from __future__ import annotations

from app.core.celery import celery_app

if __name__ == "__main__":
    celery_app.start()
