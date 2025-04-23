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
        self.kafka_topic = os.environ.get("KAFKA_TOPIC", "sensor-data")

        # Simulation settings
        self.num_sensors = int(os.environ.get("NUM_SENSORS", "20"))
        self.simulation_interval_ms = int(
            os.environ.get("SIMULATION_INTERVAL_MS", "1000")
        )

        # Data settings
        self.data_file = os.environ.get("SENSOR_DATA_FILE", "data_sensors.csv")

        # Log all configuration values at startup
        self._log_config()

    def _log_config(self):
        """Log all configuration values for debugging."""
        logger.info("Application configuration:")
        logger.info(f"  KAFKA_BOOTSTRAP_SERVERS: {self.kafka_bootstrap_servers}")
        logger.info(f"  KAFKA_TOPIC: {self.kafka_topic}")
        logger.info(f"  SIMULATION_INTERVAL_MS: {self.simulation_interval_ms}")
        logger.info(f"  SENSOR_DATA_FILE: {self.data_file}")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "kafka_bootstrap_servers": self.kafka_bootstrap_servers,
            "kafka_topic": self.kafka_topic,
            "num_sensors": self.num_sensors,
            "simulation_interval_ms": self.simulation_interval_ms,
            "data_file": self.data_file,
        }


config = Config()
