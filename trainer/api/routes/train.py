"""
Training job endpoints for the ML Training Service.

This module provides API endpoints for triggering training jobs,
checking their status, and retrieving results.
"""

from fastapi import APIRouter
from loguru import logger

from trainer.api.models import JobStatus, TrainingResponse
from trainer.tasks import train_model

router = APIRouter()


@router.post("/train", response_model=TrainingResponse)
async def trigger_training():
    """
    Trigger a new training job.

    This endpoint starts a new model training process using Celery
    and returns a job ID that can be used to check progress. The job
    runs asynchronously, so this endpoint returns immediately while
    the training continues in the background.

    Returns:
        `TrainingResponse`: Object containing the job ID, initial status ("queued"),
            and a descriptive message
    """
    task = train_model.delay()
    job_id = task.id

    logger.info(f"Training job {job_id} queued")

    return TrainingResponse(
        job_id=job_id, status="queued", message="Training job has been queued"
    )


@router.get("/train/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Get the status of a training job.

    This endpoint checks the current status of a previously submitted
    training job. It translates Celery task states into user-friendly
    status messages and includes result information when available.

    Args:
        job_id (`str`): The ID of the training job to check

    Returns:
        `JobStatus`: Object containing the job status, and either result
            information (if completed) or error details (if failed)
    """
    task = train_model.AsyncResult(job_id)

    if task.state == "PENDING":
        return JobStatus(job_id=job_id, status="queued")

    elif task.state == "STARTED":
        return JobStatus(job_id=job_id, status="running")

    elif task.state == "SUCCESS":
        return JobStatus(
            job_id=job_id,
            status="completed",
            result=task.result.get("result") if task.result else None,
        )

    elif task.state == "FAILURE":
        return JobStatus(
            job_id=job_id,
            status="failed",
            error=str(task.result.get("error") if task.result else "Unknown error"),
        )

    else:
        return JobStatus(job_id=job_id, status=task.state.lower())
