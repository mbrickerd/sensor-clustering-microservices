# Trainer Service

This directory contains the ML training service for the Sensor Failure Detection System. This service analyses sensor data, trains clustering models, and manages the ML lifecycle through MLflow.

**Table of contents**
- [Trainer Service](#trainer-service)
  - [Overview](#overview)
  - [Directory Structure](#directory-structure)
  - [Dockerfile Explanation](#dockerfile-explanation)
  - [Environment Variables](#environment-variables)
  - [Operational Modes](#operational-modes)
  - [Key Components](#key-components)
  - [Training Pipeline](#training-pipeline)
  - [API Endpoints](#api-endpoints)
  - [Worker and Celery Integration](#worker-and-celery-integration)
  - [MLflow Integration](#mlflow-integration)
  - [Integration with Microservices](#integration-with-microservices)
  - [Troubleshooting](#troubleshooting)

## Overview

The trainer service is the core machine learning component of the Sensor Failure Detection System:
- Retrieves historical sensor readings and failure data from the database
- Processes and analyses data to extract meaningful features
- Performs clustering to identify patterns in machine failures
- Trains and evaluates models using KMeans clustering
- Stores trained models in MLflow's model registry
- Provides a REST API for triggering training jobs and monitoring training status
- Supports async distributed processing via Celery workers
- Notifies other services when new models are available

## Directory Structure

```
trainer/
├── Dockerfile                # Multi-stage Docker build
├── README.md                 # This documentation file
├── __init__.py               # Package initialisation
├── api/                      # API components
│   ├── __init__.py
│   ├── models/               # API data models
│   │   ├── __init__.py
│   │   ├── health.py         # Health check response models
│   │   ├── status.py         # Job status models
│   │   └── train.py          # Training request/response models
│   └── routes/               # API endpoints
│       ├── __init__.py
│       ├── health.py         # Health check endpoint
│       └── train.py          # Training endpoints
├── app.py                    # Main application & FastAPI entry point
├── celery.py                 # Celery worker configuration
├── config.py                 # Configuration from environment variables
├── pyproject.toml            # Project dependencies
├── scripts/                  # Helper scripts
│   └── entrypoint.sh         # Container entrypoint script
├── services/                 # Core service implementations
│   ├── __init__.py
│   └── trainer.py            # Main trainer implementation
└── tasks/                    # Celery task definitions
    ├── __init__.py
    └── train.py              # Training task implementation
```

## Dockerfile Explanation

The Dockerfile creates a multi-mode service container:

```dockerfile
FROM python:3.10-slim AS builder

WORKDIR /app

COPY domain/ /app/domain/
COPY trainer/ /app/trainer/

RUN pip install uv
RUN cd /app/domain && uv pip install --system -e .
RUN cd /app/trainer && uv pip install --system -e .

FROM python:3.10-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/domain ./domain
COPY --from=builder /app/trainer ./trainer
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENV PYTHONPATH=/app
RUN mkdir -p /app/data

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
```

Key aspects:
- Uses Python 3.10 slim image for both build and runtime stages
- Contains conditional startup logic for three operational modes:
  - API mode: Starts FastAPI server with uvicorn
  - Worker mode: Starts Celery worker
  - Direct mode: Runs trainer directly
- Includes curl for health checks
- Mounts domain module as dependency

## Environment Variables

| Environment Variable | Description | Default | Required |
| -------------------- | ----------- | ------- | -------- |
| `MLFLOW_TRACKING_URI` | URI for MLflow server | http://mlflow:5000 | Yes |
| `POSTGRES_HOST` | PostgreSQL server hostname | localhost | Yes |
| `POSTGRES_PORT` | PostgreSQL server port | 5432 | Yes |
| `POSTGRES_USER` | PostgreSQL username | sensor_user | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | sensor_password | Yes |
| `POSTGRES_DB` | PostgreSQL database name | sensor_data | Yes |
| `REDIS_HOST` | Redis hostname for Celery | redis | For worker mode |
| `REDIS_PORT` | Redis port for Celery | 6379 | For worker mode |
| `API_MODE` | Whether to run in API mode | false | No |
| `WORKER_MODE` | Whether to run in worker mode | false | No |
| `TRAINING_LOOKBACK_HOURS` | Hours of historical data to use | 1 | No |
| `MODEL_F1_THRESHOLD` | Threshold for model quality | 0.7 | No |
| `N_CLUSTERS` | Number of clusters for KMeans | 3 | No |
| `SENSOR_DATA_FILE` | Path to reference data file | data_sensors.csv | Yes |

## Operational Modes

The trainer service can operate in three distinct modes:

1. **API Mode (`API_MODE=true`)**
   - Runs as a FastAPI web server on port 8000
   - Provides endpoints for triggering training and checking status
   - Used by Airflow to orchestrate training
   - Delegates actual training to Celery workers

2. **Worker Mode (`WORKER_MODE=true`)**
   - Runs as a Celery worker
   - Processes training jobs from the queue
   - Performs the actual training computation
   - Communicates with MLflow and the database

3. **Direct Mode (default)**
   - Runs the training pipeline directly
   - Used for debugging or one-off training
   - No API or worker infrastructure

## Key Components

The service consists of several key components:

1. **TrainerService (`trainer.py`)**
   - Main service that implements the clustering workflow
   - Loads and processes data from the database
   - Extracts features for clustering
   - Trains KMeans models and evaluates performance
   - Logs models and artifacts to MLflow
   - Stores results in the database

2. **API Routes (`routes/`)**
   - `health.py`: Provides system health monitoring
   - `train.py`: Endpoints for starting training jobs and checking status

3. **Celery Setup (`celery.py`)**
   - Configures Celery for distributed task processing
   - Sets up Redis connection for broker and backend
   - Defines serialization formats

4. **API Models (`models/`)**
   - Pydantic models for request/response validation
   - Ensures type safety and data validation

## Training Pipeline

The trainer implements a complete ML pipeline:

1. **Data Collection**
   - Retrieves failure episodes from the database
   - Lookback period is configurable (`TRAINING_LOOKBACK_HOURS`)
   - Groups sensor readings by failure episodes

2. **Feature Extraction**
   - Calculates statistical features from sensor data
   - Computes mean, standard deviation, min, max for each sensor
   - Standardises features for clustering

3. **Model Training**
   - Applies KMeans clustering algorithm with configurable clusters
   - Evaluates model quality with silhouette score
   - Compares clusters to known failure patterns (if available)

4. **Results Analysis**
   - Identifies distinctive features for each cluster
   - Creates cluster profiles for interpretation
   - Compares clusters to labeled patterns from reference data

5. **Model Management**
   - Logs model and artifacts to MLflow
   - Registers model in MLflow model registry
   - Creates database record for the model
   - Marks new model as active
   - Signals predictor service about new model

## API Endpoints

The service exposes these REST API endpoints:

1. **Health Check**
   - **URL**: `/api/health`
   - **Method**: `GET`
   - **Response**: `{"status": "healthy", "version": "1.0.0"}`
   - **Purpose**: Service health monitoring

2. **Start Training**
   - **URL**: `/api/train`
   - **Method**: `POST`
   - **Body**: `{"parameters": {...}}` (optional)
   - **Response**: `{"job_id": "123", "status": "queued", "message": "Training job submitted"}`
   - **Purpose**: Trigger a new training job

3. **Check Training Status**
   - **URL**: `/api/train/{job_id}`
   - **Method**: `GET`
   - **Response**: `{"job_id": "123", "status": "completed|running|failed", "result": "...", "error": "..."}`
   - **Purpose**: Monitor training job progress

## Worker and Celery Integration

The service uses Celery for asynchronous processing:

- **Task Queue**: Redis serves as broker for job distribution
- **Work Delegation**: API submits tasks to the queue
- **Workers**: Separate containers process tasks from the queue
- **State Management**: Redis backend stores task results
- **Monitoring**: Health checks ensure worker availability
- **Scalability**: Multiple workers can process jobs in parallel

## MLflow Integration

The service integrates deeply with MLflow:

1. **Tracking Server Connection**
   - Connects to MLflow server at `MLFLOW_TRACKING_URI`
   - Creates experiment if it doesn't exist

2. **Experiment Tracking**
   - Logs parameters: `n_clusters`, `n_failures`, `training_lookback_hours`
   - Logs metrics: `silhouette_score`
   - Logs artifacts: trained model, scaler, cluster profiles

3. **Model Registry**
   - Registers model as "sensor_failure_clustering"
   - Versions models automatically
   - Sets "production" alias for latest model

4. **Artifact Storage**
   - Saves model artifacts to MLflow's artifact store
   - Includes KMeans model, scaler, and cluster profiles

## Integration with Microservices

The trainer service integrates with these components:

1. **PostgreSQL Database**
   - Reads sensor readings and failure data
   - Stores trained model metadata
   - Signals model availability

2. **MLflow**
   - Logs training runs and model artifacts
   - Manages model versions
   - Provides model registry

3. **Airflow**
   - Orchestrates training schedule
   - Triggers training via API
   - Monitors training progress

4. **Predictor Service**
   - Consumes trained models
   - Receives signals about new models
   - Uses models for inference

5. **Redis**
   - Serves as Celery broker
   - Manages distributed task queue
   - Stores task results

Data flow:
1. Consumer service stores sensor data in PostgreSQL
2. Airflow triggers training via trainer API
3. Trainer worker processes data and trains model
4. Model is stored in MLflow and registered
5. Model version is recorded in database
6. Predictor service is notified of new model
7. Predictor loads new model for inference

## Troubleshooting

Common issues and their solutions:

1. **Training fails with database errors**
   - Check PostgreSQL connection parameters
   - Verify that the database has sensor data
   - Increase `TRAINING_LOOKBACK_HOURS` if insufficient data
   - Check database logs: `docker logs postgres`

2. **MLflow integration issues**
   - Ensure MLflow server is running: `docker ps | grep mlflow`
   - Verify MLflow connection URI is correct
   - Check MLflow logs: `docker logs mlflow`
   - Verify PostgreSQL permissions for MLflow backend store

3. **Celery worker problems**
   - Verify Redis is running: `docker ps | grep redis`
   - Check worker logs: `docker logs sensor-worker`
   - Test Redis connectivity: `docker exec redis redis-cli ping`
   - Restart the worker if needed

4. **API availability issues**
   - Check API container health: `docker ps | grep sensor-trainer`
   - Verify uvicorn is running: `docker logs sensor-trainer | grep uvicorn`
   - Test API directly: `curl http://localhost:8000/api/health`
   - Check port mappings in docker-compose.yml

5. **Model quality issues**
   - Check silhouette score in MLflow UI
   - Adjust `N_CLUSTERS` parameter
   - Increase `TRAINING_LOOKBACK_HOURS` for more data
   - Review cluster profiles in MLflow artifacts
