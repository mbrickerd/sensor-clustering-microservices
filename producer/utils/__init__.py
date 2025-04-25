"""
Utility modules for the Sensor Data Producer Service.

This package contains utility functions used by the producer service,
primarily for analysing reference data and extracting statistical
properties for simulation.
"""

from .analysis import (
    analyse_dataset,
    analyse_failure_patterns,
    calculate_sensor_statistics,
    get_default_failure_patterns,
    get_default_sensor_statistics,
)

__all__ = [
    "calculate_sensor_statistics",
    "analyse_failure_patterns",
    "get_default_sensor_statistics",
    "get_default_failure_patterns",
    "analyse_dataset",
]
