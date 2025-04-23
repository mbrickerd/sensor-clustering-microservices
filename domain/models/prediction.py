from tortoise.fields import (
    CharField,
    IntField, 
    FloatField, 
    DatetimeField, 
    ForeignKeyField, 
    CASCADE
)
from tortoise.models import Model


class SensorPrediction(Model):
    """Model representing a prediction for a sensor reading."""
    id = IntField(pk=True)
    cluster_id = IntField()
    model_version = CharField(max_length=50)
    confidence_score = FloatField(null=True)
    prediction_time = DatetimeField(auto_now_add=True)
    mlflow_run_id = CharField(max_length=50, null=True)
    model_name = CharField(max_length=100, null=True, default="sensor_failure_clustering")
    
    reading = ForeignKeyField(
        "models.SensorReading", related_name="predictions", on_delete=CASCADE
    )
    
    class Meta:
        table = "predictions"
        unique_together = ("reading", "model_version")
        ordering = ["-prediction_time"]
    
    def __str__(self):
        return f"Prediction for reading {self.reading_id}: cluster {self.cluster_id}"