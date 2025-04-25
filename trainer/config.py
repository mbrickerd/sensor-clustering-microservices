"""
Configuration module for the ML Training Service.

This module loads and manages configuration settings from environment
variables, providing a centralised point for accessing configuration
values throughout the training service application.
"""

import os

from loguru import logger


class Config:
    """
    Central configuration class for the ML services.

    This class manages all configuration settings for the training service,
    including MLflow connection parameters, PostgreSQL database settings,
    training parameters, and notification settings. Default values are
    provided for all settings but can be overridden through environment
    variables.
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

        self.data_file = os.environ.get("SENSOR_DATA_FILE", "data_sensors.csv")

        self.postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
        self.postgres_port = int(os.environ.get("POSTGRES_PORT", "5432"))
        self.postgres_user = os.environ.get("POSTGRES_USER", "sensor_user")
        self.postgres_password = os.environ.get("POSTGRES_PASSWORD", "sensor_password")
        self.postgres_db = os.environ.get("POSTGRES_DB", "sensor_data")

        self.training_lookback_hours = int(
            os.environ.get("TRAINING_LOOKBACK_HOURS", "1")
        )
        self.model_f1_threshold = float(os.environ.get("MODEL_F1_THRESHOLD", "0.7"))
        self.n_clusters = int(os.environ.get("N_CLUSTERS", "3"))
        self.prediction_batch_size = int(os.environ.get("PREDICTION_BATCH_SIZE", "100"))
        self.drift_detection_window = int(
            os.environ.get("DRIFT_DETECTION_WINDOW", "1000")
        )
        self.drift_threshold = float(os.environ.get("DRIFT_THRESHOLD", "0.05"))

        self.enable_notifications = (
            os.environ.get("ENABLE_NOTIFICATIONS", "True").lower() == "true"
        )
        self.notification_endpoint = os.environ.get("NOTIFICATION_ENDPOINT", "")

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
        logger.info("ML Service configuration:")
        logger.info(f"  MLFLOW_TRACKING_URI: {self.mlflow_tracking_uri}")
        logger.info(f"  SENSOR_DATA_FILE: {self.data_file}")
        logger.info(f"  POSTGRES_HOST: {self.postgres_host}")
        logger.info(f"  POSTGRES_PORT: {self.postgres_port}")
        logger.info(f"  POSTGRES_USER: {self.postgres_user}")
        logger.info(f"  POSTGRES_DB: {self.postgres_db}")
        logger.info(f"  TRAINING_LOOKBACK_HOURS: {self.training_lookback_hours}")
        logger.info(f"  MODEL_F1_THRESHOLD: {self.model_f1_threshold}")
        logger.info(f"  PREDICTION_BATCH_SIZE: {self.prediction_batch_size}")
        logger.info(f"  DRIFT_DETECTION_WINDOW: {self.drift_detection_window}")
        logger.info(f"  DRIFT_THRESHOLD: {self.drift_threshold}")
        logger.info(f"  ENABLE_NOTIFICATIONS: {self.enable_notifications}")

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
