from tortoise.fields import CharField, DatetimeField, IntField, ReverseRelation
from tortoise.models import Model


class Machine(Model):
    """Model representing a machine."""

    id = IntField(pk=True)
    machine_id = CharField(max_length=36, unique=True)
    first_seen = DatetimeField(auto_now_add=True)
    last_seen = DatetimeField(auto_now=True)

    # Relationships
    readings = ReverseRelation["SensorReading"]
    failures = ReverseRelation["Failure"]

    class Meta:
        table = "machines"

    def __str__(self) -> str:
        return f"Machine {self.machine_id}"
