from fastapi import APIRouter
from trainer.api.models.train import TrainingResponse
from trainer.api.models.status import JobStatus
from trainer.tasks.train import train_model
from loguru import logger


router = APIRouter()


@router.post("/train", response_model=TrainingResponse)
async def trigger_training():
    """
    Trigger a new training job
    
    This endpoint starts a new model training process using Celery
    and returns a job ID that can be used to check progress.
    """
    task = train_model.delay()
    job_id = task.id
    
    logger.info(f"Training job {job_id} queued")
    
    return TrainingResponse(
        job_id=job_id,
        status="queued",
        message="Training job has been queued"
    )

@router.get("/train/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    task = train_model.AsyncResult(job_id)
    
    if task.state == 'PENDING':
        return JobStatus(job_id=job_id, status="queued")
    elif task.state == 'STARTED':
        return JobStatus(job_id=job_id, status="running")
    elif task.state == 'SUCCESS':
        return JobStatus(
            job_id=job_id,
            status="completed",
            result=task.result.get("result") if task.result else None
        )
    elif task.state == 'FAILURE':
        return JobStatus(
            job_id=job_id,
            status="failed",
            error=str(task.result.get("error") if task.result else "Unknown error")
        )
    else:
        return JobStatus(job_id=job_id, status=task.state.lower())