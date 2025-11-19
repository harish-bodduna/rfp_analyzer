"""Celery application configuration."""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "rfp_analyzer",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_default_queue="rfp_analyzer",
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
