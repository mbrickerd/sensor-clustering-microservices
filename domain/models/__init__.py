from tortoise import Tortoise

from .cluster import Cluster
from .drift import DriftEvent
from .failure import Failure
from .machine import Machine
from .prediction import SensorPrediction
from .reading import SensorReading
from .version import ModelVersion

__all__ = [
    "Machine",
    "SensorReading",
    "Failure",
    "Cluster",
    "SensorPrediction",
    "DriftEvent",
    "ModelVersion",
]


async def init_db(db_url: str):
    """Initialize the database connection."""
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["domain.models"]},
    )
    await Tortoise.generate_schemas()
