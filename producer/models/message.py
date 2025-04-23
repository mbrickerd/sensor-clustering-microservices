from pydantic import BaseModel
from .reading import SensorReading


class SensorMessage(BaseModel):
    """Model for Kafka messages"""
    machine_id: str
    timestamp: str
    readings: SensorReading