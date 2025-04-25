"""
Message models for the Sensor Data Producer Service.

This module defines the structure of messages that are published
to Kafka, combining machine identifiers, timestamps, and sensor
reading data.
"""

from pydantic import BaseModel

from .reading import SensorReading


class SensorMessage(BaseModel):
    """
    Model for Kafka messages.

    This class represents the complete message structure that is
    published to Kafka. It includes identification information
    for the machine, a timestamp, and the sensor reading data.

    Attributes:
        machine_id (`str`): Unique identifier for the machine
        timestamp (`str`): ISO format timestamp of when the reading was taken
        readings (`SensorReading`): The sensor reading data and failure indicator
    """

    machine_id: str
    timestamp: str
    readings: SensorReading
