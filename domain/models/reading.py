import json

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
    """Model representing a sensor reading."""

    id = IntField(pk=True)
    timestamp = DatetimeField()
    values = JSONField()

    machine = ForeignKeyField(
        "models.Machine", related_name="readings", on_delete=CASCADE
    )
    failure = ForeignKeyField(
        "models.Failure", related_name="readings", on_delete=SET_NULL, null=True
    )

    class Meta:
        table = "readings"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Reading for {self.machine_id} at {self.timestamp}"

    @property
    def values_dict(self) -> dict[str, float]:
        """Get sensor values as a dictionary."""
        if isinstance(self.values, str):
            return json.loads(self.values)

        return self.values
