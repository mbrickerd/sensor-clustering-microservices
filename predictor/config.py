import os
from loguru import logger
from typing import Any


class Config:
    """Configuration for the inference service."""

    def __init__(self):
        """Initialize configuration with values from environment variables."""
        # MLflow settings
        self.mlflow_tracking_uri = os.environ.get(
            "MLFLOW_TRACKING_URI", "http://mlflow:5000"
        )
        
        # PostgreSQL settings (reusing from consumer config)
        self.postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
        self.postgres_port = int(os.environ.get("POSTGRES_PORT", "5432"))
        self.postgres_user = os.environ.get("POSTGRES_USER", "sensor_user")
        self.postgres_password = os.environ.get("POSTGRES_PASSWORD", "sensor_password")
        self.postgres_db = os.environ.get("POSTGRES_DB", "sensor_data")
        
        # Inference settings
        self.training_lookback_hours = int(os.environ.get("TRAINING_LOOKBACK_HOURS", "1"))
        self.prediction_batch_size = int(os.environ.get("PREDICTION_BATCH_SIZE", "100"))
        self.inference_interval_seconds = int(os.environ.get("INFERENCE_INTERVAL_SECONDS", "30"))
        self.drift_threshold = float(os.environ.get("DRIFT_THRESHOLD", "0.1"))
        
        # Drift detection settings
        self.drift_detection_window = int(os.environ.get("DRIFT_DETECTION_WINDOW", "100"))
        self.metrics_port = int(os.environ.get("METRICS_PORT", "8001"))

        # Log all configuration values at startup
        self._log_config()

    def _log_config(self):
        """Log all configuration values for debugging."""
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
            "prediction_batch_size": self.prediction_batch_size,
            "inference_interval_seconds": self.inference_interval_seconds,
            "drift_threshold": self.drift_threshold,
        }


config = Config()