"""
Status models for the ML Training Service API.

This module defines the data structure for job status responses.
"""

from pydantic import BaseModel


class JobStatus(BaseModel):
    """
    Job status response model.

    This class represents the status of a training job, including
    its current state, results (if available), and any error information.

    Attributes:
        job_id (`str`): Unique identifier for the job
        status (`str`): Current status of the job ("pending", "running", "completed", "failed")
        result (`str`, optional): Results of the job, if completed successfully
        error (`str`, optional): Error message if the job failed
    """

    job_id: str
    status: str
    result: str | None = None
    error: str | None = None
