"""
Health check endpoint for the ML Training Service.

This module provides a simple health check endpoint that returns
the status of the service and version information.
"""

from fastapi import APIRouter

from trainer.api.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Service health check endpoint.

    This endpoint provides a basic health check for the training service,
    returning a status indicator that can be used by monitoring systems
    to verify that the service is operational.

    Returns:
        `HealthResponse`: Object containing service status ("healthy") and version
    """
    return HealthResponse(status="healthy")
