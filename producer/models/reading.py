"""
Reading models for the Sensor Data Producer Service.

This module defines the structure of sensor readings, including
the sensor values and failure indicator.
"""

from pydantic import BaseModel


class SensorReading(BaseModel):
    """
    Model for sensor readings data.

    This class represents a set of sensor readings from a machine
    at a specific point in time, along with an indicator of whether
    the machine is experiencing a failure.

    Attributes:
        readings (`dict[str, float]`): Dictionary mapping sensor names to their values
        has_failure (`bool`): Indicator of whether a failure is active
    """

    readings: dict[str, float]
    has_failure: bool
