import os
import requests
import time
from loguru import logger


def mlflow_healthcheck():
    """Check if MLflow server is healthy by hitting the root endpoint."""
    mlflow_uri = os.environ.get('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
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


def trainer_healthcheck():
    """Check if the trainer API is healthy."""
    trainer_uri = os.environ.get('AIRFLOW_CONN_TRAINER_API')
    if trainer_uri.startswith('http:'):
        trainer_uri = trainer_uri
    
    logger.info(f"Checking trainer API health at: {trainer_uri}")
    
    max_retries = 5
    retry_interval = 5  # seconds
    
    for i in range(max_retries):
        try:
            response = requests.get(f"{trainer_uri.rstrip('/')}/api/health", timeout=10)
            logger.info(f"Trainer API response status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("Trainer API is healthy")
                return True
            
        except Exception as err:
            logger.warning(f"Trainer API check failed (attempt {i+1}/{max_retries}): {err}")
            
        time.sleep(retry_interval)
    
    raise Exception("Trainer API health check failed after all retries")