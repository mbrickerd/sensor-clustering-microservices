"""
Sensor reading representation for the Sensor Failure Detection System.

This module defines the SensorReading model that stores sensor measurements
collected from machines, including their timestamp and values.
"""

import json
from typing import cast

from tortoise.fields import (
    CASCADE,
    SET_NULL,
    DatetimeField,
    ForeignKeyField,
    IntField,
    JSONField,
)
from tortoise.models import Model


class SensorReading(Model):
    """
    Model representing a sensor reading.

    This class stores sensor measurements collected from machines. Each reading
    includes a timestamp, the sensor values as a JSON object, and references
    to the source machine and any active failure at the time of the reading.

    Attributes:
        id (`int`): Primary key
        timestamp (`datetime`): When the reading was taken
        values (`JSONField`): Sensor measurements stored as a JSON object
        machine (`ForeignKey`): Reference to the machine that produced this reading
        failure (`ForeignKey`, optional): Reference to an active failure, if any
    """

    id: IntField = IntField(pk=True, description="Primary key")
    timestamp: DatetimeField = DatetimeField(description="When the reading was taken")
    values: JSONField = JSONField(
        description="Sensor measurements stored as a JSON object"
    )

    machine = ForeignKeyField(
        "models.Machine",
        related_name="readings",
        on_delete=CASCADE,
        description="Reference to the machine that produced this reading",
    )  # type: ignore
    failure = ForeignKeyField(
        "models.Failure",
        related_name="readings",
        on_delete=SET_NULL,
        null=True,
        description="Reference to an active failure, if any",
    )  # type: ignore

    class Meta:
        table = "readings"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"Reading for {self.id} at {self.timestamp}"

    @property
    def values_dict(self) -> dict[str, float]:
        """
        Get sensor values as a dictionary.

        This property ensures that the sensor values are always returned as a
        dictionary, regardless of whether they are stored as a JSON string
        or a dictionary object.

        Returns:
            `dict[str, float]`: Dictionary mapping sensor names to their values
        """
        if isinstance(self.values, str):
            return cast(dict[str, float], json.loads(self.values))

        return cast(dict[str, float], self.values)
