from celery import Celery
import os


redis_host = os.environ.get("REDIS_HOST")
redis_port = os.environ.get("REDIS_PORT")
redis_url = f"redis://{redis_host}:{redis_port}/0"

celery = Celery(
    'trainer_tasks',
    broker=redis_url,
    backend=redis_url
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)