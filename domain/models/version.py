from tortoise.fields import (
    CharField,
    IntField, 
    DatetimeField, 
    BooleanField, 
)
from tortoise.models import Model


class ModelVersion(Model):
    """Tracks when new model versions are available"""
    id = IntField(pk=True)
    version = CharField(max_length=50)
    run_id = CharField(max_length=50)
    created_at = DatetimeField(auto_now_add=True)
    is_processed = BooleanField(default=False)

    class Meta:
        table = "versions"