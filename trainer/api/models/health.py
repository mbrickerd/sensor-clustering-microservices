"""
Health check models for the ML Training Service API.

This module defines the data structure for health check responses.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """
    Health check response model.

    This class represents the response format for the health check endpoint,
    indicating the current service status and version information.

    Attributes:
        status (`str`): Current status of the service ("healthy", "degraded", etc.)
        version (`str`): Current version of the service, defaults to "1.0.0"
    """

    status: str
    version: str = "1.0.0"
