"""
Domain models for the Sensor Failure Detection System.

This package provides a centralised definition of all database entities used
throughout the Sensor Failure Detection System, ensuring consistency across
microservices. It leverages Tortoise ORM for object-relational mapping with
PostgreSQL and provides a unified database initialisation function.

This package serves as a single source of truth for data models across all
microservices in the system, eliminating duplication and enforcing consistency.
"""

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


async def init_db(db_url: str) -> None:
    """
    Initialise the database connection and create schemas if needed.

    This function establishes a connection to the PostgreSQL database using
    the provided connection URL and creates any missing tables based on
    the models defined in this package. All microservices use this function
    to establish their database connections.

    Args:
        db_url (`str`): PostgreSQL connection URL in the format
            `postgres://user:password@host:port/dbname`

    Returns:
        `None`

    Raises:
        `ConfigurationError`: If the database connection cannot be established
        `OperationalError`: If there's an issue creating the schema
    """
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["domain.models"]},
    )
    await Tortoise.generate_schemas()
