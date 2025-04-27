# Airflow

This directory contains the custom Airflow image configuration for the Sensor Failure Detection System. This image provides workflow orchestration for ML pipeline tasks, including sensor data processing, model training, and inference.

**Table of contents**
- [Airflow](#airflow)
  - [Overview](#overview)
  - [Directory Structure](#directory-structure)
  - [Dockerfile Explanation](#dockerfile-explanation)
  - [Environment Variables](#environment-variables)
  - [Services in docker-compose.yml](#services-in-docker-composeyml)
  - [Custom DAGs](#custom-dags)
  - [Connections and Variables](#connections-and-variables)
  - [Troubleshooting](#troubleshooting)

## Overview

The Airflow component orchestrates the data processing and ML workflow pipelines. It schedules and manages:
- Sensor data validation
- Model training pipelines
- Model evaluation and registration

## Directory Structure

```
airflow/
├── Dockerfile      # Custom Airflow image definition
└── README.md       # This documentation file
```

The actual DAG files are mounted from the root `dags/` directory when the containers are run via `docker-compose`.

## Dockerfile Explanation

The Dockerfile builds a custom Airflow image with the necessary dependencies for our ML workflow:

```dockerfile
FROM apache/airflow:2.8.4-python3.10

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY domain/ /opt/airflow/domain/
COPY trainer/ /opt/airflow/trainer/
COPY trainer/pyproject.toml /opt/airflow/

WORKDIR /opt/airflow

RUN mkdir -p /opt/airflow/domain/sensor_domain.egg-info \
    && mkdir -p /opt/airflow/trainer/sensor_trainer.egg-info \
    && chmod -R 777 /opt/airflow/domain \
    && chmod -R 777 /opt/airflow/trainer

USER airflow

RUN pip install --user uv psycopg2-binary pendulum
RUN cd domain && python -m pip install --user -e .
RUN sed -i 's|/app/domain|/opt/airflow/domain|g' /opt/airflow/trainer/pyproject.toml
RUN cd trainer && python -m pip install --user -e .

ENV PYTHONPATH=/opt/airflow:${PYTHONPATH}
```

Key aspects:
- Based on Apache Airflow 2.8.4 with Python 3.10
- Installs system dependencies
- Incorporates our custom domain and trainer modules
- Sets up proper permissions and directory structures
- Installs Python dependencies with `uv`
- Configures `PYTHONPATH` to access our custom modules

## Environment Variables

| Environment Variable | Description | Required |
| -------------------- | ----------- | -------- |
| `AIRFLOW__CORE__EXECUTOR` | The executor to use (`LocalExecutor` in this setup) | Yes |
| `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` | PostgreSQL connection string | Yes |
| `AIRFLOW__CORE__LOAD_EXAMPLES` | Whether to load example DAGs | No (default: `false`) |
| `AIRFLOW__WEBSERVER__SECRET_KEY` | Secret key for the Airflow webserver | Yes |
| `AIRFLOW_CONN_TRAINER_API` | Connection URI for the `sensor-trainer` API | Yes |
| `MLFLOW_TRACKING_URI` | URI for MLflow tracking server | Yes |
| `AIRFLOW_USERNAME` | Username for Airflow web UI | For initialisation |
| `AIRFLOW_PASSWORD` | Password for Airflow web UI | For initialisation |

## Services in `docker-compose.yml`

The custom Airflow image is used by three services defined in the root `docker-compose.yml`:

1. **airflow-init**
   - One-time initialisation service
   - Sets up the metadata database
   - Creates admin user account
   - Runs `airflow db init` command

2. **airflow-webserver**
   - Serves the Airflow UI on port 8081
   - Mounts DAGs, logs, and application code
   - Provides task monitoring and management interface
   - Command: `webserver`

3. **airflow-scheduler**
   - Schedules and triggers workflow execution
   - Monitors the DAG directory for changes
   - Handles task dependencies
   - Command: `scheduler`

All three services use the same custom image but with different commands and configurations.

## Custom DAGs

Place DAG files in the `/dags` directory. The primary workflow is focused on training:

**Training DAG**: Orchestrates model training
   - Data extraction and validation
   - Feature engineering
   - Model training and tuning
   - Model evaluation and registration in MLflow

Note that inference is handled by the dedicated `sensor-predictor` service rather than through Airflow DAGs.

## Connections and Variables

Required Airflow connections:

| Connection ID | Type | Description |
| ------------- | ---- | ----------- |
| `trainer_api` | HTTP | Connection to the `sensor-trainer` API |
| `postgres_conn` | Postgres | Connection to the main PostgreSQL database |
| `mlflow_conn` | HTTP | Connection to the MLflow tracking server |

Common variables:

| Variable | Description |
| -------- | ----------- |
| `model_registry_name` | Name of the model in MLflow registry |
| `training_lookback_days` | Days of historical data to use for training |
| `prediction_threshold` | Confidence threshold for failure predictions |

## Troubleshooting

Common issues and their solutions:

1. **Missing modules in DAGs**
   - Check if the domain and trainer modules are properly installed
   - Verify `PYTHONPATH` in the container: `docker exec airflow-webserver env | grep PYTHON`

2. **DAGs not appearing in the UI**
   - Check file permissions and ownership
   - Verify Python syntax with: `docker exec airflow-webserver python -m py_compile /opt/airflow/dags/your_dag.py`
   - Check scheduler logs: `docker logs airflow-scheduler`

3. **Connection issues with external services**
   - Verify network connectivity between containers
   - Check connection configurations in Airflow UI
   - Ensure services are healthy in `docker-compose`
