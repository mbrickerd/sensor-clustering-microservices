"""
Clustering model representation for the Sensor Failure Detection System.

This module defines the Cluster model that stores information about
trained clustering models, including their performance metrics, parameters,
and MLflow tracking information.
"""

from tortoise.fields import (
    BooleanField,
    CharField,
    DatetimeField,
    FloatField,
    IntField,
    JSONField,
)
from tortoise.models import Model


class Cluster(Model):
    """
    Model representing a trained clustering model.

    This class stores information about clustering models that have been
    trained on sensor data. It includes references to the MLflow run where
    the model is tracked, performance metrics such as silhouette score,
    and the profiles of each identified cluster.

    Attributes:
        id (`int`): Primary key
        mlflow_run_id (`str`): Unique identifier for the MLflow run where this model is tracked
        mlflow_model_version (`int`): MLflow model registry version number
        created_at (`datetime`): Timestamp when this record was created
        is_active (`bool`): Whether this is the currently active clustering model
        n_clusters (`int`): Number of clusters in this model
        silhouette_score (`float`): Clustering quality metric
        cluster_profiles (`dict`): JSON representation of the cluster centroids and characteristics
    """

    id = IntField(pk=True, description="Primary key")
    mlflow_run_id = CharField(
        max_length=36,
        unique=True,
        description="Unique identifier for the MLflow run where this model is tracked",
    )
    mlflow_model_version = IntField(description="MLflow model registry version number")
    created_at = DatetimeField(
        auto_now_add=True, description="Timestamp when this record was created"
    )
    is_active = BooleanField(
        default=False,
        description="Whether this is the currently active clustering model",
    )
    n_clusters = IntField(description="Number of clusters in this model")
    silhouette_score = FloatField(description="Clustering quality metric")
    cluster_profiles = JSONField(
        description="JSON representation of the cluster centroids and characteristics"
    )

    class Meta:
        table = "clusters"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Cluster {self.id} (Run: {self.mlflow_run_id})"
