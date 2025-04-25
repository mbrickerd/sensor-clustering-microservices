# Predictor Service

This directory contains the ML prediction service for the Sensor Failure Detection System. This service loads trained clustering models from MLflow and provides real-time inference on sensor data.

**Table of contents**
- [Predictor Service](#predictor-service)
  - [Overview](#overview)
  - [Directory Structure](#directory-structure)
  - [Dockerfile Explanation](#dockerfile-explanation)
  - [Environment Variables](#environment-variables)
  - [Key Components](#key-components)
  - [Prediction Workflow](#prediction-workflow)
  - [Drift Detection](#drift-detection)
  - [Metrics Exposed](#metrics-exposed)
  - [Integration with Microservices](#integration-with-microservices)
  - [Troubleshooting](#troubleshooting)

## Overview

The predictor service is responsible for the inference part of the ML pipeline in the Sensor Failure Detection System. It:
- Loads trained clustering models from MLflow
- Processes new sensor readings from the database
- Predicts cluster assignments for sensor readings
- Detects data drift and alerts when distribution changes
- Exposes Prometheus metrics for monitoring
- Automatically updates when new models are deployed

## Directory Structure

```
predictor/
├── Dockerfile                 # Multi-stage Docker build
├── README.md                  # This documentation file
├── __init__.py
├── app.py                     # Main application entry point
├── config.py                  # Configuration from environment variables
├── pyproject.toml             # Project dependencies
└── services/
    ├── __init__.py
    ├── drift.py               # Drift detection service
    └── predictor.py           # Main prediction service
```

## Dockerfile Explanation

The Dockerfile uses a multi-stage build to optimise the image size:

```dockerfile
FROM python:3.10-slim AS builder

WORKDIR /app

COPY domain/ /app/domain/

COPY predictor/ /app/predictor/

RUN mkdir -p /app/domain/domain /app/predictor/predictor
RUN touch /app/domain/domain/__init__.py /app/predictor/predictor/__init__.py

RUN pip install uv
RUN cd /app/domain && uv pip install --system -e .
RUN cd /app/predictor && uv pip install --system -e .

FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /app/domain ./domain
COPY --from=builder /app/predictor ./predictor
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENV PYTHONPATH=/app
RUN mkdir -p /app/data

EXPOSE 8001

CMD ["python", "-m", "predictor.app"]
```

Key aspects:
- Uses Python 3.10 slim image for both build and runtime stages
- Includes the `domain` module as a dependency
- Uses `uv` for dependency management
- Exposes port 8001 for Prometheus metrics
- Sets the proper `PYTHONPATH` for module imports

## Environment Variables

| Environment Variable | Description | Default | Required |
| -------------------- | ----------- | ------- | -------- |
| `MLFLOW_TRACKING_URI` | URI for MLflow server | http://mlflow:5000 | Yes |
| `POSTGRES_HOST` | PostgreSQL server hostname | localhost | Yes |
| `POSTGRES_PORT` | PostgreSQL server port | 5432 | Yes |
| `POSTGRES_USER` | PostgreSQL username | sensor_user | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | sensor_password | Yes |
| `POSTGRES_DB` | PostgreSQL database name | sensor_data | Yes |
| `PREDICTION_BATCH_SIZE` | Number of readings to process in each batch | 100 | No |
| `INFERENCE_INTERVAL_SECONDS` | Delay between inference cycles | 30 | No |
| `DRIFT_THRESHOLD` | Threshold for drift detection (0-1) | 0.1 | No |
| `DRIFT_DETECTION_WINDOW` | Size of sliding window for drift detection | 100 | No |
| `METRICS_PORT` | Port for Prometheus metrics | 8001 | No |

## Key Components

The predictor service consists of two main components:

1. **Predictor Service (`predictor.py`)**
   - Loads clustering models from MLflow
   - Extracts features from sensor readings
   - Makes cluster predictions
   - Stores prediction results in the database
   - Handles model updates

2. **Drift Detection Service (`drift.py`)**
   - Monitors prediction distributions
   - Detects shifts using Jensen-Shannon divergence
   - Records drift events in the database
   - Exposes Prometheus metrics
   - Provides visualisation data for Grafana

## Prediction Workflow

The prediction process follows these steps:

1. **Model Loading**
   - Query database for active model information
   - Load model artifacts from MLflow (KMeans model, scaler)
   - Extract feature definitions from model metadata

2. **Batch Processing**
   - Query database for unprocessed sensor readings
   - Extract features matching the model's expected input
   - Apply preprocessing (scaling) to features
   - Make cluster predictions

3. **Result Storage**
   - Store prediction results in the database
   - Link predictions to original readings
   - Include model version information

4. **Model Updates**
   - Check for new model version notifications
   - Automatically reload models when a new version is deployed
   - Maintain backward compatibility with older readings

## Drift Detection

The service includes real-time drift detection:

- Uses a sliding window approach to track prediction distributions
- Compares current distribution to a reference distribution
- Calculates Jensen-Shannon divergence as a drift score (0-1)
- Triggers alerts when the drift score exceeds the threshold
- Records drift events for further analysis
- Provides metrics for visualisation in Grafana

## Metrics Exposed

The service exposes the following Prometheus metrics:

| Metric Name | Type | Description |
| ----------- | ---- | ----------- |
| `sensor_predictions_total` | Counter | Total number of predictions made |
| `sensor_predictions_by_cluster` | Counter | Predictions by cluster ID |
| `sensor_drift_score` | Gauge | Current drift score (0-1) |
| `sensor_drift_detected` | Gauge | Binary flag (1=drift detected, 0=normal) |
| `sensor_prediction_latency_seconds` | Histogram | Prediction latency distribution |

These metrics are available at `http://localhost:8001/` and are visualised in the Grafana dashboard.

## Integration with Microservices

The predictor service integrates with these components:

1. **PostgreSQL Database**
   - Reads sensor readings to process
   - Stores prediction results
   - Records drift events
   - Tracks model version information

2. **MLflow**
   - Loads trained models and artifacts
   - Gets model metadata and version information
   - Ensures model provenance and reproducibility

3. **Prometheus**
   - Exposes metrics for monitoring
   - Provides alerting capabilities
   - Enables performance tracking

4. **Grafana**
   - Visualises prediction distributions
   - Displays drift metrics over time
   - Provides monitoring dashboards

5. **Domain Models**
   - Shares database models with other services
   - Ensures consistent data representation

## Troubleshooting

Common issues and their solutions:

1. **Missing model or failed model loading**
   - Check MLflow server availability
   - Verify that an active model exists in the database
   - Ensure proper MLflow run ID in the database
   - Check for proper artifact paths in MLflow

2. **No predictions being made**
   - Verify that new sensor readings are being added to the database
   - Check for database connectivity issues
   - Ensure the model has been successfully loaded
   - Verify feature extraction is working correctly

3. **High prediction latency**
   - Consider increasing the batch size
   - Check database performance (indexes)
   - Monitor system resources (CPU, memory)
   - Consider horizontal scaling for high volumes

4. **False drift detection**
   - Adjust the drift threshold parameter
   - Increase the drift detection window size
   - Verify reference distribution accuracy
   - Consider using more robust drift metrics
