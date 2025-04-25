"""
Configuration module for the Sensor Data Producer Service.

This module loads and manages configuration settings from environment
variables, providing a centralised point for accessing configuration
values throughout the producer service application.
"""

import os

from loguru import logger


class Config:
    """
    Central configuration class that loads settings from environment variables.

    This class manages all configuration settings for the producer service,
    including Kafka connection parameters, simulation settings, and data source
    paths. Default values are provided for all settings but can be overridden
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
        self.kafka_bootstrap_servers = os.environ.get(
            "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
        )
        self.kafka_topic = os.environ.get("KAFKA_TOPIC", "sensor-data")
        self.num_sensors = int(os.environ.get("NUM_SENSORS", "20"))
        self.simulation_interval_ms = int(
            os.environ.get("SIMULATION_INTERVAL_MS", "1000")
        )
        self.data_file = os.environ.get("SENSOR_DATA_FILE", "data_sensors.csv")

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
        logger.info("Application configuration:")
        logger.info(f"  KAFKA_BOOTSTRAP_SERVERS: {self.kafka_bootstrap_servers}")
        logger.info(f"  KAFKA_TOPIC: {self.kafka_topic}")
        logger.info(f"  SIMULATION_INTERVAL_MS: {self.simulation_interval_ms}")
        logger.info(f"  SENSOR_DATA_FILE: {self.data_file}")


config = Config()
