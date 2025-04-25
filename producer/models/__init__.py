"""
Data models for the Sensor Data Producer Service.

This package provides Pydantic models that define the structure of
the sensor data and messages published to Kafka. These models ensure
consistent data formats and validation throughout the application.
"""

from .failure import FailureInfo
from .message import SensorMessage
from .reading import SensorReading

__all__ = ["SensorReading", "SensorMessage", "FailureInfo"]
