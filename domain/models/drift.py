"""
Drift detection events for the Sensor Failure Detection System.

This module defines the DriftEvent model that records detected
data drift between the reference data distribution (used for training)
and the current data distribution observed in production.
"""

from tortoise.fields import DatetimeField, FloatField, IntField, JSONField
from tortoise.models import Model


class DriftEvent(Model):
    """
    Model representing a detected drift event.

    This class stores information about detected data drift events,
    which occur when the distribution of sensor data changes significantly
    from the distribution used to train the models. These events may
    trigger retraining of models or alerts to operators.

    Attributes:
        id (`int`): Primary key
        detection_time (`datetime`): When the drift was detected
        drift_score (`float`): Quantitative measure of drift magnitude
        reference_distribution (`dict`): Statistical summary of the reference distribution
        current_distribution (`dict`): Statistical summary of the current distribution
    """

    id = IntField(pk=True, description="Primary key")
    detection_time = DatetimeField(
        auto_now_add=True, description="When the drift was detected"
    )
    drift_score = FloatField(description="Quantitative measure of drift magnitude")
    reference_distribution = JSONField(
        description="Statistical summary of the reference distribution"
    )
    current_distribution = JSONField(
        description="Statistical summary of the current distribution"
    )

    class Meta:
        table = "drift"
        ordering = ["-detection_time"]

    def __str__(self) -> str:
        return f"Drift event at {self.detection_time} (score: {self.drift_score})"
