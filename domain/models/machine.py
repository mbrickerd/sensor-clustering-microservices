"""
Machine entity representation for the Sensor Failure Detection System.

This module defines the Machine model that represents physical machines
being monitored by the system.
"""

from tortoise.fields import CharField, DatetimeField, IntField, ReverseRelation
from tortoise.models import Model


class Machine(Model):
    """
    Model representing a machine.

    This class represents a physical machine that is being monitored by the
    system. Each machine is identified by a unique machine_id and has
    timestamps tracking when it was first seen and last seen by the system.

    Attributes:
        id (`int`): Primary key
        machine_id (`str`): Unique external identifier for the machine
        first_seen (`datetime`): When this machine was first registered in the system
        last_seen (`datetime`): When this machine was last active
        readings (`ReverseRelation`): Access to all sensor readings from this machine
        failures (`ReverseRelation`): Access to all failure events for this machine
    """

    id = IntField(pk=True, description="Primary key")
    machine_id = CharField(
        max_length=36,
        unique=True,
        description="Unique external identifier for the machine",
    )
    first_seen = DatetimeField(
        auto_now_add=True,
        description="When this machine was first registered in the system",
    )
    last_seen = DatetimeField(
        auto_now=True, description="When this machine was last active"
    )

    readings = ReverseRelation["SensorReading"]
    failures = ReverseRelation["Failure"]

    class Meta:
        table = "machines"

    def __str__(self) -> str:
        return f"Machine {self.machine_id}"
