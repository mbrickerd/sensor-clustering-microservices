from tortoise.fields import (
    IntField, 
    FloatField, 
    DatetimeField, 
    JSONField
)
from tortoise.models import Model


class DriftEvent(Model):
    """Model representing a detected drift event."""
    id = IntField(pk=True)
    detection_time = DatetimeField(auto_now_add=True)
    drift_score = FloatField()
    reference_distribution = JSONField()
    current_distribution = JSONField()
    
    class Meta:
        table = "drift"
        ordering = ["-detection_time"]
    
    def __str__(self) -> str:
        return f"Drift event at {self.detection_time} (score: {self.drift_score})"