# Domain Models

This directory contains the shared domain models for the Sensor Failure Detection System. These models represent the core data structures used across all microservices in the system.

**Table of contents**
- [Domain Models](#domain-models)
  - [Overview](#overview)
  - [Directory Structure](#directory-structure)
  - [Data Models](#data-models)
  - [Database Integration](#database-integration)
  - [Usage in Microservices](#usage-in-microservices)
  - [Package Management](#package-management)
  - [Development Guidelines](#development-guidelines)
  - [Troubleshooting](#troubleshooting)

## Overview

The domain models package provides a centralised definition of all database entities used throughout the Sensor Failure Detection System. This ensures consistency across microservices, eliminates duplication, and enforces a single source of truth for the data model.

Key features:
- Object-Relational Mapping (ORM) using [Tortoise ORM](https://tortoise.github.io/)
- Consistent data types and relationships
- Shared models across all microservices
- Type-hinted for better IDE support and code quality

## Directory Structure

```
domain/
├── models/
│   ├── __init__.py           # Model exports and DB initialisation
│   ├── cluster.py            # Clustering model definition
│   ├── drift.py              # Drift detection events
│   ├── failure.py            # Machine failure episodes
│   ├── machine.py            # Machine entity
│   ├── prediction.py         # ML predictions
│   ├── reading.py            # Sensor readings
│   └── version.py            # Model version tracking
├── py.typed                  # PEP 561 marker for type checking
├── pyproject.toml            # Package definition
├── Dockerfile                # Used by other services' multi-stage builds
└── README.md                 # This documentation file
```

## Data Models

The package defines the following models:

1. **Machine**: Represents physical machines being monitored
   ```python
   class Machine(Model):
       id = IntField(pk=True)
       machine_id = CharField(max_length=36, unique=True)
       first_seen = DatetimeField(auto_now_add=True)
       last_seen = DatetimeField(auto_now=True)
   ```

2. **SensorReading**: Contains individual sensor measurements
   ```python
   class SensorReading(Model):
       id = IntField(pk=True)
       timestamp = DatetimeField()
       values = JSONField()           # Stores all sensor values as JSON
       machine = ForeignKeyField("models.Machine", related_name="readings")
       failure = ForeignKeyField("models.Failure", null=True)
   ```

3. **Failure**: Represents a failure episode on a machine
   ```python
   class Failure(Model):
       id = IntField(pk=True)
       start_time = DatetimeField()
       end_time = DatetimeField(null=True)
       is_active = BooleanField(default=True)
       machine = ForeignKeyField("models.Machine", related_name="failures")
   ```

4. **Cluster**: Stores information about trained clustering models
   ```python
   class Cluster(Model):
       id = IntField(pk=True)
       mlflow_run_id = CharField(max_length=36, unique=True)
       mlflow_model_version = IntField()
       created_at = DatetimeField(auto_now_add=True)
       is_active = BooleanField(default=False)
       n_clusters = IntField()
       silhouette_score = FloatField()
       cluster_profiles = JSONField()
   ```

5. **SensorPrediction**: Stores predictions made by ML models
   ```python
   class SensorPrediction(Model):
       id = IntField(pk=True)
       cluster_id = IntField()
       model_version = CharField(max_length=50)
       confidence_score = FloatField(null=True)
       prediction_time = DatetimeField(auto_now_add=True)
       reading = ForeignKeyField("models.SensorReading", related_name="predictions")
   ```

6. **DriftEvent**: Records detected data drift events
   ```python
   class DriftEvent(Model):
       id = IntField(pk=True)
       detection_time = DatetimeField(auto_now_add=True)
       drift_score = FloatField()
       reference_distribution = JSONField()
       current_distribution = JSONField()
   ```

7. **ModelVersion**: Tracks new model versions
   ```python
   class ModelVersion(Model):
       id = IntField(pk=True)
       version = CharField(max_length=50)
       run_id = CharField(max_length=50)
       created_at = DatetimeField(auto_now_add=True)
       is_processed = BooleanField(default=False)
   ```

## Database Integration

The package provides a unified database initialisation function:

```python
async def init_db(db_url: str) -> None:
    """Initialise the database connection."""
    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["domain.models"]},
    )
    await Tortoise.generate_schemas()
```

This function is used by all microservices to connect to the database and create any missing tables.

## Usage in Microservices

This domain models package is a core dependency used across all microservices in the system:

1. **Producer Service**:
   - Imports `Machine` model to identify data sources
   - References the data schema for generating synthetic data

2. **Consumer Service**:
   - Uses `Machine`, `SensorReading`, and `Failure` models
   - Stores incoming sensor data and tracks failure events

3. **Trainer Service**:
   - Queries `SensorReading` and `Failure` data for training
   - Creates and updates `Cluster` models for new trained models
   - Manages `ModelVersion` records for tracking

4. **Predictor Service**:
   - Reads `SensorReading` data to make predictions
   - Creates `SensorPrediction` records
   - Manages `DriftEvent` records for model monitoring

The package is included in each service's Dockerfile, typically in a multi-stage build pattern:

```dockerfile
COPY domain/ /app/domain/

RUN cd /app/domain && uv pip install --system -e .
```

## Package Management

The package is defined in `pyproject.toml`:

```toml
[project]
name = "sensor-domain"
version = "0.1.0"
description = "Domain models for sensor failure detection system"
requires-python = ">=3.10"
dependencies = [
    "tortoise-orm>=0.25.0",
]
```

And is installed as an editable package in each service, allowing for:
- Direct imports from `domain.models`
- Single source of truth for model definitions
- Simplified dependency management
- Type-checking support via `py.typed`

## Development Guidelines

When modifying the domain models:

1. **Maintain backward compatibility** whenever possible
2. **Update all services** that depend on modified models
3. **Add migrations** for schema changes (see Tortoise ORM documentation)
4. **Update type hints** to ensure correct static analysis
5. **Test changes** across all dependent services

## Troubleshooting

Common issues and their solutions:

1. **Database schema conflicts**
   - Ensure all services are using the same version of the domain package
   - Run migrations to update the schema manually if needed
   - Check for differences between development and production schemas

2. **Import errors**
   - Verify PYTHONPATH includes the domain package
   - Check that the package is installed with `pip list | grep sensor-domain`
   - Ensure proper dependency declaration in service pyproject.toml files

3. **Type checking issues**
   - Make sure the `py.typed` file is present
   - Verify that type hints are up-to-date
   - Use `mypy` to catch type-related issues early
