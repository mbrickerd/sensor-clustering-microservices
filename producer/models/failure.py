from pydantic import BaseModel


class FailureInfo(BaseModel):
    """Model for failure information"""
    time: int
    duration: int