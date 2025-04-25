"""
Celery configuration for the ML Training Service.

This module configures Celery for distributed task processing,
connecting to Redis as the message broker and result backend.
It sets up serialization formats and timezone settings.
"""

import os

from celery import Celery

redis_host = os.environ.get("REDIS_HOST")
redis_port = os.environ.get("REDIS_PORT")
redis_url = f"redis://{redis_host}:{redis_port}/0"

celery = Celery("trainer_tasks", broker=redis_url, backend=redis_url)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
