"""
Health check utilities for the Airflow DAGs.

This module provides functions to verify the health and availability of
services required by the training workflows, such as MLflow and the trainer API.
Each function includes retry mechanisms to handle temporary service outages.
"""

import os
import time

import requests
from loguru import logger


def mlflow_healthcheck() -> bool:
    """
    Check if MLflow server is healthy by hitting the root endpoint.

    This function attempts to connect to the MLflow server specified by the
    `MLFLOW_TRACKING_URI` environment variable. It retries up to 5 times with
    a 5-second interval between retries.

    Returns:
        `bool`: `True` if the MLflow server is healthy

    Raises:
        `Exception`: If all health check attempts fail
    """
    mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    logger.info(f"Checking MLflow health at: {mlflow_uri}")

    max_retries = 5
    retry_interval = 5  # seconds

    for i in range(max_retries):
        try:
            response = requests.get(f"{mlflow_uri.rstrip('/')}/", timeout=10)
            logger.info(f"MLflow response status: {response.status_code}")

            if response.status_code == 200:
                logger.info("MLflow server is healthy")
                return True

        except Exception as err:
            logger.warning(f"MLflow check failed (attempt {i+1}/{max_retries}): {err}")

        time.sleep(retry_interval)

    raise Exception("MLflow server health check failed after all retries")


def trainer_healthcheck() -> bool:
    """
    Check if the trainer API is healthy.

    This function attempts to connect to the trainer API specified by the
    `AIRFLOW_CONN_TRAINER_API` environment variable. It sends a request to
    the `/api/health` endpoint and retries up to 5 times with a 5-second
    interval between retries.

    Returns:
        `bool`: `True` if the trainer API is healthy

    Raises:
        `Exception`: If all health check attempts fail
    """
    trainer_uri = os.environ.get("AIRFLOW_CONN_TRAINER_API", "http://trainer:8000")
    if trainer_uri.startswith("http:"):
        trainer_uri = trainer_uri

    logger.info(f"Checking trainer API health at: {trainer_uri}")

    max_retries = 5
    retry_interval = 5

    for i in range(max_retries):
        try:
            response = requests.get(f"{trainer_uri.rstrip('/')}/api/health", timeout=10)
            logger.info(f"Trainer API response status: {response.status_code}")

            if response.status_code == 200:
                logger.info("Trainer API is healthy")
                return True

        except Exception as err:
            logger.warning(
                f"Trainer API check failed (attempt {i+1}/{max_retries}): {err}"
            )

        time.sleep(retry_interval)

    raise Exception("Trainer API health check failed after all retries")
