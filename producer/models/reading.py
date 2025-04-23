from pydantic import BaseModel


class SensorReading(BaseModel):
    """Model for sensor readings data"""
    readings: dict[str, float]
    has_failure: bool