import os
from typing import Any, Dict

from loguru import logger


class Config:
    """Central configuration class that loads settings from environment variables."""

    def __init__(self):
        """Initialize configuration with values from environment variables."""
        # Kafka settings
        self.kafka_bootstrap_servers = os.environ.get(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self.kafka_topic = os.environ.get("KAFKA_TOPIC", "machine.sensor.readings")
        self.kafka_group_id = os.environ.get("KAFKA_GROUP_ID", "sensor-consumer-group")

        # PostgreSQL settings
        self.postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
        self.postgres_port = int(os.environ.get("POSTGRES_PORT", "5432"))
        self.postgres_user = os.environ.get("POSTGRES_USER", "sensor_user")
        self.postgres_password = os.environ.get("POSTGRES_PASSWORD", "sensor_password")
        self.postgres_db = os.environ.get("POSTGRES_DB", "sensor_data")

        # Consumer settings
        self.batch_size = int(os.environ.get("BATCH_SIZE", "100"))
        self.commit_interval_ms = int(os.environ.get("COMMIT_INTERVAL_MS", "5000"))

        # Log all configuration values at startup
        self._log_config()

    def _log_config(self):
        """Log all configuration values for debugging."""
        logger.info("Consumer configuration:")
        logger.info(f"  KAFKA_BOOTSTRAP_SERVERS: {self.kafka_bootstrap_servers}")
        logger.info(f"  KAFKA_TOPIC: {self.kafka_topic}")
        logger.info(f"  KAFKA_GROUP_ID: {self.kafka_group_id}")
        logger.info(f"  POSTGRES_HOST: {self.postgres_host}")
        logger.info(f"  POSTGRES_PORT: {self.postgres_port}")
        logger.info(f"  POSTGRES_USER: {self.postgres_user}")
        logger.info(f"  POSTGRES_DB: {self.postgres_db}")
        logger.info(f"  BATCH_SIZE: {self.batch_size}")
        logger.info(f"  COMMIT_INTERVAL_MS: {self.commit_interval_ms}")

    def get_postgres_uri(self) -> str:
        """Get the PostgreSQL connection URI."""
        return (
            f"postgres://{self.postgres_user}"
            f":{self.postgres_password}@{self.postgres_host}"
            f":{self.postgres_port}/{self.postgres_db}"
        )

    def as_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "kafka_bootstrap_servers": self.kafka_bootstrap_servers,
            "kafka_topic": self.kafka_topic,
            "kafka_group_id": self.kafka_group_id,
            "postgres_host": self.postgres_host,
            "postgres_port": self.postgres_port,
            "postgres_user": self.postgres_user,
            "postgres_db": self.postgres_db,
            "batch_size": self.batch_size,
            "commit_interval_ms": self.commit_interval_ms,
        }


config = Config()
