"""
ML prediction representation for the Sensor Failure Detection System.

This module defines the SensorPrediction model that stores the results
of machine learning predictions made on sensor readings.
"""

from tortoise.fields import (
    CASCADE,
    CharField,
    DatetimeField,
    FloatField,
    ForeignKeyField,
    IntField,
)
from tortoise.models import Model


class SensorPrediction(Model):
    """
    Model representing a prediction for a sensor reading.

    This class stores the results of machine learning predictions made
    on sensor readings. Each prediction associates a reading with a
    specific cluster identified by the model and includes metadata
    about the model version used and confidence scores.

    Attributes:
        id (`int`): Primary key
        cluster_id (`int`): Identifier of the predicted cluster
        model_version (`str`): Version of the model used for prediction
        confidence_score (`float`, optional): Confidence level of the prediction
        prediction_time (`datetime`): When the prediction was made
        mlflow_run_id (`str`, optional): MLflow run ID of the model used
        model_name (`str`): Name of the machine learning model
        reading (ForeignKey): Reference to the sensor reading being predicted
    """

    id = IntField(pk=True, description="Primary key")
    cluster_id = IntField(description="Identifier of the predicted cluster")
    model_version = CharField(
        max_length=50, description="Version of the model used for prediction"
    )
    confidence_score = FloatField(
        null=True, description="Confidence level of the prediction"
    )
    prediction_time = DatetimeField(
        auto_now_add=True, description="When the prediction was made"
    )
    mlflow_run_id = CharField(
        max_length=50, null=True, description="MLflow run ID of the model used"
    )
    model_name = CharField(
        max_length=100,
        null=True,
        default="sensor_failure_clustering",
        description="Name of the machine learning model",
    )

    reading = ForeignKeyField(
        "models.SensorReading",
        related_name="predictions",
        on_delete=CASCADE,
        description="Reference to the sensor reading being predicted",
    )

    class Meta:
        table = "predictions"
        unique_together = ("reading", "model_version")
        ordering = ["-prediction_time"]

    def __str__(self) -> str:
        return f"Prediction for reading {self.reading_id}: cluster {self.cluster_id}"
