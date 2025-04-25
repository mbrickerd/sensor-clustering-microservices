"""
Failure models for the Sensor Data Producer Service.

This module defines the data structure for representing machine
failures in the simulation, including their timing information.
"""

from pydantic import BaseModel


class FailureInfo(BaseModel):
    """
    Model for failure information.

    This class represents an active failure in the simulation, tracking
    the current time counter of the failure and its total duration.
    When time reaches duration, the failure is considered resolved.

    Attributes:
        time (int): Current time counter since the failure started
        duration (int): Total duration that the failure will last
    """

    time: int
    duration: int
