from tortoise.fields import (
    IntField, 
    CharField, 
    DatetimeField, 
    JSONField, 
    FloatField,
    BooleanField
)
from tortoise.models import Model


class Cluster(Model):
    """Model representing a trained clustering model."""
    id = IntField(pk=True)
    mlflow_run_id = CharField(max_length=36, unique=True)
    mlflow_model_version = IntField()
    created_at = DatetimeField(auto_now_add=True)
    is_active = BooleanField(default=False)
    n_clusters = IntField()
    silhouette_score = FloatField()
    cluster_profiles = JSONField()
    
    class Meta:
        table = "clusters"
        ordering = ["-created_at"]
    
    def __str__(self) -> str:
        return f"Cluster {self.id} (Run: {self.mlflow_run_id})"