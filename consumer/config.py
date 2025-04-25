"""
Configuration module for the Sensor Data Consumer Service.

This module loads and manages configuration settings from environment
variables, providing a centralised point for accessing configuration
values throughout the application.
"""

import os

from loguru import logger


class Config:
    """
    Central configuration class that loads settings from environment variables.

    This class manages all configuration settings for the consumer service,
    including Kafka connection parameters, PostgreSQL database settings,
    and consumer-specific options. Default values are provided for all
    settings but can be overridden through environment variables.
    """

    def __init__(self) -> None:
        """
        Initialise configuration with values from environment variables.

        Loads and validates all configuration settings from environment
        variables, providing default values when environment variables
        are not present. All configuration values are logged at startup.

        Returns:
            `None`
        """
        self.kafka_bootstrap_servers = os.environ.get(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self.kafka_topic = os.environ.get("KAFKA_TOPIC", "machine.sensor.readings")
        self.kafka_group_id = os.environ.get("KAFKA_GROUP_ID", "sensor-consumer-group")

        self.postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
        self.postgres_port = int(os.environ.get("POSTGRES_PORT", "5432"))
        self.postgres_user = os.environ.get("POSTGRES_USER", "sensor_user")
        self.postgres_password = os.environ.get("POSTGRES_PASSWORD", "sensor_password")
        self.postgres_db = os.environ.get("POSTGRES_DB", "sensor_data")

        self.batch_size = int(os.environ.get("BATCH_SIZE", "100"))
        self.commit_interval_ms = int(os.environ.get("COMMIT_INTERVAL_MS", "5000"))

        self._log_config()

    def _log_config(self) -> None:
        """
        Log all configuration values for debugging.

        Outputs all configuration values to the application log at the
        INFO level for transparency and debugging purposes.

        Returns:
            `None`
        """
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
