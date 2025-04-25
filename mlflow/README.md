# MLflow

This directory contains the MLflow configuration for the Sensor Failure Detection System. MLflow provides model tracking, registry, and artifact storage for machine learning models.

**Table of contents**
- [MLflow](#mlflow)
  - [Overview](#overview)
  - [Directory Structure](#directory-structure)
  - [Dockerfile Explanation](#dockerfile-explanation)
  - [Environment Variables](#environment-variables)
  - [Integration with Microservices](#integration-with-microservices)
  - [Model Lifecycle](#model-lifecycle)
  - [Artifact Storage](#artifact-storage)
  - [Accessing the MLflow UI](#accessing-the-mlflow-ui)
  - [Troubleshooting](#troubleshooting)

## Overview

The MLflow component provides model lifecycle management for the Sensor Failure Detection System:
- Experiment tracking for model training runs
- Metrics and parameter logging
- Model versioning and registry
- Artifact storage for trained models
- REST API for model serving

## Directory Structure

```
mlflow/
├── Dockerfile      # Custom MLflow image definition
└── README.md       # This documentation file
```

The MLflow artifacts are stored in a persistent volume mounted at `/mlflow/artifacts`.

## Dockerfile Explanation

The Dockerfile builds a custom MLflow image with PostgreSQL support:

```dockerfile
FROM ghcr.io/mlflow/mlflow:v2.21.3 AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        curl && \
    rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir psycopg2-binary gunicorn

FROM ghcr.io/mlflow/mlflow:v2.21.3

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
```

Key aspects:
- Uses a multi-stage build to reduce image size
- Based on the official MLflow 2.21.3 image
- Adds PostgreSQL support via `psycopg2-binary`
- Uses `gunicorn` for improved production performance
- Includes `curl` for health checks
- Optimised for minimal image size

## Environment Variables

| Environment Variable | Description | Required |
| -------------------- | ----------- | -------- |
| `MLFLOW_BACKEND_STORE_URI` | PostgreSQL connection string for model metadata | Yes |
| `MLFLOW_TRACKING_URI` | URI for other services to connect to MLflow | For clients |

The service configuration in `docker-compose.yml`:

```yaml
mlflow:
  build:
    context: .
    dockerfile: mlflow/Dockerfile
  container_name: mlflow
  depends_on:
    postgres:
      condition: service_healthy
  ports:
    - "5001:5000"
  environment:
    MLFLOW_BACKEND_STORE_URI: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
  volumes:
    - ./data:/app/data
    - mlflow_data:/mlflow/artifacts
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:5000 || exit 1"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 60s
  networks:
    - sensor_network
```

## Integration with Microservices

MLflow integrates with several components in the system:

1. **Sensor Trainer Service**
   - Logs training runs and metrics to MLflow
   - Registers new model versions
   - Stores model artifacts
   - Uses MLflow APIs for experiment tracking

2. **Sensor Predictor Service**
   - Loads models from MLflow model registry
   - Fetches the latest active model version
   - Uses models for inference

3. **Airflow**
   - Monitors MLflow for new model versions
   - Coordinates model training pipelines
   - Verifies model quality before promotion

The data flow typically follows this pattern:
1. Trainer trains a new model and logs to MLflow
2. MLflow stores metrics and model artifacts
3. New model version is registered in MLflow
4. Predictor fetches the latest model from MLflow
5. Predictor uses the model for inference

## Model Lifecycle

The model lifecycle managed by MLflow includes:

1. **Training & Logging**
   - Training parameters and hyperparameters
   - Performance metrics (silhouette score, etc.)
   - Model artifacts (clusters, profiles)

2. **Registration**
   - Models are registered with a unique name
   - Each training creates a new version
   - Versions track lineage and provenance

3. **Deployment**
   - Models are promoted to "Production" stage
   - Predictor service uses the latest production model
   - Previous versions are archived

## Artifact Storage

MLflow stores artifacts in a persistent volume:

- Model artifacts are stored in `/mlflow/artifacts`
- PostgreSQL stores metadata about experiments and runs
- Large binary files (trained models) are stored in the filesystem
- Artifacts include model files, cluster profiles, and metadata

## Accessing the MLflow UI

The MLflow web interface is accessible through:

- **URL**: http://localhost:5001
- **Default page**: Experiments list
- **Key features**:
  - Experiment tracking
  - Run comparison
  - Model registry
  - Artifact visualisation

## Troubleshooting

Common issues and their solutions:

1. **Connection issues**
   - Check PostgreSQL connection: `docker logs mlflow | grep "connection"`
   - Verify network connectivity: `docker exec mlflow curl -s postgres:5432`
   - Ensure PostgreSQL is healthy: `docker ps | grep postgres`

2. **Missing models or experiments**
   - Check database migrations: `docker exec mlflow mlflow db upgrade $MLFLOW_BACKEND_STORE_URI`
   - Verify storage permissions: `docker exec mlflow ls -la /mlflow/artifacts`
   - Check for database connectivity issues

3. **Slow performance**
   - Monitor PostgreSQL performance
   - Check artifact storage volume space
   - Consider optimising gunicorn workers: `mlflow server --workers=4`

4. **API errors from other services**
   - Verify MLFLOW_TRACKING_URI is consistent across services
   - Check MLflow server logs: `docker logs mlflow`
   - Test API connectivity: `docker exec sensor-trainer curl -s mlflow:5000/api/2.0/mlflow/experiments/list`
