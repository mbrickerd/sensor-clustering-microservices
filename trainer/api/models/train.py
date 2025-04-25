"""
Training models for the ML Training Service API.

This module defines the data structures for training job
requests and responses.
"""

from typing import Any

from pydantic import BaseModel


class TrainingRequest(BaseModel):
    """
    Training job request model.

    This class represents the request format for starting a new training job,
    including optional configuration parameters to customise the training process.

    Attributes:
        parameters (`dict[str, Any]`, optional): Optional configuration parameters
            to customise the training job
    """

    parameters: dict[str, Any] | None = None


class TrainingResponse(BaseModel):
    """
    Training job response model.

    This class represents the response format when a training job is initiated,
    providing a job identifier that can be used to check the status later.

    Attributes:
        job_id (`str`): Unique identifier for the training job
        status (`str`): Initial status of the job (typically "pending" or "running")
        message (`str`): Human-readable message about the job creation
    """

    job_id: str
    status: str
    message: str
