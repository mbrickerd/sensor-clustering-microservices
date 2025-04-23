from tortoise.fields import (
    IntField, 
    DatetimeField, 
    BooleanField, 
    ForeignKeyField, 
    ReverseRelation, 
    CASCADE,
)
from tortoise.models import Model


class Failure(Model):
    """Model representing a machine failure."""
    id = IntField(pk=True)
    
    start_time = DatetimeField()
    end_time = DatetimeField(null=True)
    is_active = BooleanField(default=True)
    
    # Relationship to machine
    machine = ForeignKeyField(
        "models.Machine", related_name="failures", on_delete=CASCADE
    )
    
    # Reverse relation to readings
    readings = ReverseRelation["SensorReading"]
    
    class Meta:
        table = "failures"
        ordering = ["-start_time"]
    
    def __str__(self):
        return f"Failure on {self.machine_id} from {self.start_time}"
