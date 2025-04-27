"""
Training task definitions for the ML Training Service.

This module defines Celery tasks for executing training jobs
asynchronously, with proper error handling and status tracking.
"""

import asyncio
from typing import Any

from loguru import logger

from trainer.celery import celery
from trainer.services import TrainerService


async def run() -> str:
    """
    Run the training job asynchronously.

    This function creates a new TrainerService instance and executes
    the complete training workflow. It is designed to be run within
    an asyncio event loop inside the Celery task.

    Returns:
        `str`: Status message ("success") if training completes successfully
    """
    trainer = TrainerService()
    await trainer.run()
    return "success"


@celery.task(bind=True)
def train_model(self) -> dict[str, Any]:
    """
    Celery task to train a model.

    This task executes the machine learning training workflow asynchronously
    through Celery. It initiates the training process, handles exceptions,
    and returns structured result information including success/failure status.

    The task uses `asyncio` to run the asynchronous training workflow within
    the synchronous Celery task environment.

    Args:
        self: The bound Celery task instance

    Returns:
        `dict[str, Any]`: Dictionary containing status ("completed" or "failed")
            and either result information or error details
    """
    task_id = self.request.id
    logger.info(f"Starting training task {task_id}")

    try:
        result = asyncio.run(run())
        logger.info(f"Training task {task_id} completed successfully")
        return {"status": "completed", "result": result}

    except Exception as err:
        logger.error(f"Training task {task_id} failed: {str(err)}")
        return {"status": "failed", "error": str(err)}
