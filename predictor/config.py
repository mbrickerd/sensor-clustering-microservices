"""
Configuration module for the ML Prediction Service.

This module loads and manages configuration settings from environment
variables, providing a centralised point for accessing configuration
values throughout the prediction service application.
"""

import os

from loguru import logger


class Config:
    """
    Configuration for the inference service.

    This class manages all configuration settings for the predictor service,
    including MLflow connection parameters, PostgreSQL database settings,
    prediction intervals, batch sizes, and drift detection thresholds.
    Default values are provided for all settings but can be overridden
    through environment variables.
    """

    def __init__(self) -> None:
        """
        Initialise configuration with values from environment variables.

        Loads and validates all configuration settings from environment
        variables, providing default values when environment variables
        are not present. All configuration values are logged at startup
        for transparency and debugging purposes.

        Returns:
            `None`
        """
        self.mlflow_tracking_uri = os.environ.get(
            "MLFLOW_TRACKING_URI", "http://mlflow:5000"
        )

        self.postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
        self.postgres_port = int(os.environ.get("POSTGRES_PORT", "5432"))
        self.postgres_user = os.environ.get("POSTGRES_USER", "sensor_user")
        self.postgres_password = os.environ.get("POSTGRES_PASSWORD", "sensor_password")
        self.postgres_db = os.environ.get("POSTGRES_DB", "sensor_data")

        self.training_lookback_hours = int(
            os.environ.get("TRAINING_LOOKBACK_HOURS", "1")
        )
        self.prediction_batch_size = int(os.environ.get("PREDICTION_BATCH_SIZE", "100"))
        self.inference_interval_seconds = int(
            os.environ.get("INFERENCE_INTERVAL_SECONDS", "30")
        )
        self.drift_threshold = float(os.environ.get("DRIFT_THRESHOLD", "0.1"))
        self.drift_detection_window = int(
            os.environ.get("DRIFT_DETECTION_WINDOW", "100")
        )
        self.metrics_port = int(os.environ.get("METRICS_PORT", "8001"))

        self._log_config()

    def _log_config(self) -> None:
        """
        Log all configuration values for debugging.

        Outputs all configuration values to the application log at the
        INFO level to provide transparency and assist with debugging
        configuration issues.

        Returns:
            `None`
        """
        logger.info("Inference service configuration:")
        logger.info(f"  MLFLOW_TRACKING_URI: {self.mlflow_tracking_uri}")
        logger.info(f"  POSTGRES_HOST: {self.postgres_host}")
        logger.info(f"  POSTGRES_PORT: {self.postgres_port}")
        logger.info(f"  POSTGRES_USER: {self.postgres_user}")
        logger.info(f"  POSTGRES_DB: {self.postgres_db}")
        logger.info(f"  PREDICTION_BATCH_SIZE: {self.prediction_batch_size}")
        logger.info(f"  INFERENCE_INTERVAL_SECONDS: {self.inference_interval_seconds}")
        logger.info(f"  DRIFT_THRESHOLD: {self.drift_threshold}")
        logger.info(f"  DRIFT_DETECTION_WINDOW: {self.drift_detection_window}")
        logger.info(f"  METRICS_PORT: {self.metrics_port}")

    def get_postgres_uri(self) -> str:
        """
        Get the PostgreSQL connection URI.

        Constructs a PostgreSQL connection URI from the individual
        configuration components (host, port, user, password, database).

        Returns:
            `str`: Formatted PostgreSQL connection URI
        """
        return (
            f"postgres://{self.postgres_user}"
            f":{self.postgres_password}@{self.postgres_host}"
            f":{self.postgres_port}/{self.postgres_db}"
        )


config = Config()
