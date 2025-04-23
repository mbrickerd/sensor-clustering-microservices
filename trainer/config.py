import os
from loguru import logger
from typing import Any


class Config:
    """Central configuration class for the ML services."""

    def __init__(self):
        """Initialize configuration with values from environment variables."""
        self.mlflow_tracking_uri = os.environ.get(
            "MLFLOW_TRACKING_URI", "http://mlflow:5000"
        )
        
        self.data_file = os.environ.get("SENSOR_DATA_FILE", "data_sensors.csv")
        
        # PostgreSQL settings (reusing from consumer config)
        self.postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
        self.postgres_port = int(os.environ.get("POSTGRES_PORT", "5432"))
        self.postgres_user = os.environ.get("POSTGRES_USER", "sensor_user")
        self.postgres_password = os.environ.get("POSTGRES_PASSWORD", "sensor_password")
        self.postgres_db = os.environ.get("POSTGRES_DB", "sensor_data")
        
        # Training settings
        self.training_lookback_hours = int(os.environ.get("TRAINING_LOOKBACK_HOURS", "1"))
        self.model_f1_threshold = float(os.environ.get("MODEL_F1_THRESHOLD", "0.7"))
        self.n_clusters = int(os.environ.get("N_CLUSTERS", "3"))
        # Prediction settings
        self.prediction_batch_size = int(os.environ.get("PREDICTION_BATCH_SIZE", "100"))
        self.drift_detection_window = int(os.environ.get("DRIFT_DETECTION_WINDOW", "1000"))
        self.drift_threshold = float(os.environ.get("DRIFT_THRESHOLD", "0.05"))
        
        # Notification settings
        self.enable_notifications = os.environ.get("ENABLE_NOTIFICATIONS", "True").lower() == "true"
        self.notification_endpoint = os.environ.get("NOTIFICATION_ENDPOINT", "")

        # Log all configuration values at startup
        self._log_config()

    def _log_config(self):
        """Log all configuration values for debugging."""
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
        """Get the PostgreSQL connection URI."""
        return (
            f"postgres://{self.postgres_user}" 
            f":{self.postgres_password}@{self.postgres_host}" 
            f":{self.postgres_port}/{self.postgres_db}"
        )

    def as_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "mlflow_tracking_uri": self.mlflow_tracking_uri,
            "postgres_host": self.postgres_host,
            "postgres_port": self.postgres_port,
            "postgres_user": self.postgres_user,
            "postgres_db": self.postgres_db,
            "training_lookback_hours": self.training_lookback_hours,
            "model_f1_threshold": self.model_f1_threshold,
            "prediction_batch_size": self.prediction_batch_size,
            "drift_detection_window": self.drift_detection_window,
            "drift_threshold": self.drift_threshold,
            "enable_notifications": self.enable_notifications,
        }


config = Config()