from tortoise import Tortoise

from .cluster import Cluster
from .machine import Machine
from .reading import SensorReading
from .failure import Failure
from .prediction import SensorPrediction
from .drift import DriftEvent
from .version import ModelVersion

__all__ = ["Machine", "SensorReading", "Failure", "Cluster", "SensorPrediction", "DriftEvent", "ModelVersion"]


async def init_db(db_url: str):
    """Initialize the database connection."""
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["domain.models"]},
    )
    await Tortoise.generate_schemas()