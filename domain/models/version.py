"""
Model version tracking for the Sensor Failure Detection System.

This module defines the ModelVersion model that tracks when new versions
of machine learning models become available for use in the system.
"""

from tortoise.fields import BooleanField, CharField, DatetimeField, IntField
from tortoise.models import Model


class ModelVersion(Model):
    """
    Tracks when new model versions are available.

    This class stores information about new versions of machine learning models
    that become available in the model registry. It helps the prediction service
    know when to update the models it uses for making predictions.

    Attributes:
        id (`int`): Primary key
        version (`str`): Version identifier of the model
        run_id (`str`): MLflow run ID where the model is stored
        created_at (`datetime`): When this model version was registered
        is_processed (`bool`): Whether this version has been processed by the predictor
    """

    id = IntField(pk=True, description="Primary key")
    version = CharField(max_length=50, description="Version identifier of the model")
    run_id = CharField(
        max_length=50, description="MLflow run ID where the model is stored"
    )
    created_at = DatetimeField(
        auto_now_add=True, description="When this model version was registered"
    )
    is_processed = BooleanField(
        default=False,
        description="Whether this version has been processed by the predictor",
    )

    class Meta:
        table = "versions"
