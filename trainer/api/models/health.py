from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str = "1.0.0"