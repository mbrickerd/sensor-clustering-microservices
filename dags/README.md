# Airflow DAGs

This directory contains the Airflow Directed Acyclic Graphs (DAGs) that orchestrate the ML pipelines for the Sensor Failure Detection System. These DAGs schedule and manage the training workflows for sensor data analysis and model creation.

**Table of contents**
- [Airflow DAGs](#airflow-dags)
  - [Overview](#overview)
  - [Directory Structure](#directory-structure)
  - [Training DAG](#training-dag)
  - [Utility Modules](#utility-modules)
  - [Integration with Microservices](#integration-with-microservices)
  - [Scheduling](#scheduling)
  - [Monitoring and Notifications](#monitoring-and-notifications)
  - [Troubleshooting](#troubleshooting)

## Overview

The DAGs directory contains the workflow definitions that automate the machine learning lifecycle in the Sensor Failure Detection System. The primary functions include:
- Scheduling regular model training jobs
- Ensuring dependent services are healthy before starting training
- Monitoring training job progress
- Handling failures and retries

## Directory Structure

```
dags/
├── train.py                  # Main training DAG definition
├── utils/
│   ├── __init__.py
│   ├── healthcheck.py        # Service health verification utilities
│   └── status.py             # Training job status monitoring utilities
└── README.md                 # This documentation file
```

## Training DAG

The main DAG (`train.py`) orchestrates the model training process:

```python
with DAG(
    "train_clustering_model",
    default_args=default_args,
    description="Train sensor failure clustering model every hour",
    schedule_interval="@hourly",
    catchup=False,
    is_paused_upon_creation=False,
    tags=["sensor", "ml", "training"],
) as dag:
    # Tasks defined here...
```

The DAG consists of four main tasks:

1. **`check_mlflow_health`**: Verifies that the MLflow tracking server is operational
2. **`check_trainer_health`**: Ensures the `sensor-trainer` API is available
3. **`trigger_training`**: Initiates the training job via an HTTP request to the trainer API
4. **`monitor_training`**: Polls the training job status until completion or failure

These tasks run in sequence, with each task depending on the successful completion of the previous task.

## Utility Modules

The `utils/` directory contains helper functions:

1. **healthcheck.py**: Provides functions for checking the health of dependent services
   - `mlflow_healthcheck()`: Verifies MLflow server connectivity
   - `trainer_healthcheck()`: Checks if the trainer API is responsive

2. **status.py**: Contains functions for monitoring training job status
   - `check_status()`: Polls the trainer API to check if a job has completed

These utilities support robust error handling with retry mechanisms to handle temporary service outages or network issues.

## Integration with Microservices

The DAGs integrate with several microservices in the system:

- **MLflow**: Used for experiment tracking and model registry
- **Sensor Trainer**: REST API that executes the actual training work
- **PostgreSQL**: Indirectly used by the trainer for data access
- **Redis**: Used for job queue management by the trainer service

Communication patterns:
1. DAG tasks check service health via HTTP requests
2. Training jobs are triggered through HTTP POST requests
3. Job status is monitored through HTTP GET requests
4. Training results are stored in MLflow by the trainer service

## Scheduling

The training DAG is configured to run hourly, ensuring regular model updates based on new sensor data:

```python
schedule_interval="@hourly"
```

Configuration settings:
- `catchup=False`: Only the latest scheduled run is executed
- `is_paused_upon_creation=False`: DAG starts running immediately when deployed
- `retries=3`: Each task will retry up to 3 times if it fails
- `retry_delay=timedelta(seconds=30)`: 30-second delay between retry attempts

## Monitoring and Notifications

The DAG includes monitoring mechanisms:
- HTTP response logging for debugging
- Explicit health checks before critical operations
- Job status polling with clear success/failure criteria

Logs are stored in the Airflow logs directory, which can be viewed through the Airflow web UI or directly in the logs volume.

## Troubleshooting

Common issues and their solutions:

1. **DAG not running on schedule**
   - Check Airflow scheduler logs: `docker logs airflow-scheduler`
   - Verify Airflow is running with the correct time zone
   - Check if the DAG is paused in the Airflow UI

2. **Health check tasks failing**
   - Ensure MLflow and trainer services are running
   - Check network connectivity between Airflow and other services
   - Verify environment variables for service URLs are correct

3. **Training job not completing**
   - Check trainer service logs: `docker logs sensor-trainer`
   - Verify database connectivity from the trainer service
   - Check if the trainer has access to MLflow for logging results

4. **Database access issues**
   - Check PostgreSQL connection parameters
   - Verify that the database contains sufficient training data
   - Ensure the database user has appropriate permissions
