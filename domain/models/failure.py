"""
Machine failure representation for the Sensor Failure Detection System.

This module defines the Failure model that represents episodes of
failures detected on machines based on sensor readings.
"""

from tortoise.fields import (
    CASCADE,
    BooleanField,
    DatetimeField,
    ForeignKeyField,
    IntField,
    ReverseRelation,
)
from tortoise.models import Model


class Failure(Model):
    """
    Model representing a machine failure.

    This class represents a period during which a machine was experiencing
    a failure. A failure is characterized by a start time and, if resolved,
    an end time. Active failures are those that have not yet been resolved.

    Attributes:
        id (`int`): Primary key
        start_time (`datetime`): When the failure was first detected
        end_time (`datetime`, optional): When the failure was resolved, or None if still active
        is_active (`bool`): Whether this failure is currently ongoing
        machine (`ForeignKey`): Reference to the machine experiencing the failure
        readings (`ReverseRelation`): Access to sensor readings collected during this failure
    """

    id = IntField(pk=True, description="Primary key")
    start_time = DatetimeField(description="When the failure was first detected")
    end_time = DatetimeField(
        null=True, description="When the failure was resolved, or None if still active"
    )
    is_active = BooleanField(
        default=True, description="Whether this failure is currently ongoing"
    )

    machine = ForeignKeyField(
        "models.Machine",
        related_name="failures",
        on_delete=CASCADE,
        description="Reference to the machine experiencing the failure",
    )
    readings = ReverseRelation["SensorReading"]

    class Meta:
        table = "failures"
        ordering = ["-start_time"]

    def __str__(self) -> str:
        return f"Failure on {self.machine_id} from {self.start_time}"
