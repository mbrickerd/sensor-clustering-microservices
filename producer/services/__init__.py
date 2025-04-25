"""
Service modules for the Sensor Data Producer Service.

This package contains service classes that provide the core functionality
of the producer service, including sensor data simulation and Kafka
message publishing.
"""

from .producer import SensorDataProducer

__all__ = ["SensorDataProducer"]
