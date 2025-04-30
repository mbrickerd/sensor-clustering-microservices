"""
Configuration module for the Sensor Data Producer Service.

This module loads configuration from Key Vault for sensitive data and
environment variables for non-sensitive settings.
"""

import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from loguru import logger


class Config:
    """
    Configuration for the Sensor Data Producer Service.

    Loads secrets from Key Vault and configuration from environment variables.
    """

    def __init__(self) -> None:
        """Initialize configuration from Key Vault and environment variables."""
        self.credential = DefaultAzureCredential()
        key_vault_url = os.environ.get("KEY_VAULT_URL")
        if key_vault_url:
            try:
                secret_client = SecretClient(
                    vault_url=key_vault_url, credential=self.credential
                )
                self.eventhub_connection_string = self._get_secret(
                    secret_client, "eventhub-tst-connection-string"
                )
                self.storage_account_name = self._get_secret(
                    secret_client, "storage-tst-account-name"
                )

                logger.info("Successfully loaded secrets from Key Vault")

            except Exception as err:
                logger.error(f"Failed to load secrets from Key Vault: {err}")
                raise

        else:
            logger.error("KEY_VAULT_URL not set!")
            raise

        self.eventhub_name = os.environ.get("EVENTHUB_NAME", "sensors")
        self.eventhub_namespace = os.environ.get("EVENTHUB_NAMESPACE", "")
        self.num_sensors = int(os.environ.get("NUM_SENSORS", "20"))
        self.simulation_interval_ms = int(
            os.environ.get("SIMULATION_INTERVAL_MS", "1000")
        )
        self.data_file = os.environ.get("SENSOR_DATA_FILE", "data_sensors.csv")
        self.storage_container = os.environ.get("STORAGE_CONTAINER", "data")

        self._log_config()

    def _get_secret(self, client: SecretClient, secret_name: str) -> str:
        """Get a secret from Key Vault, handling errors."""
        try:
            secret_value: str = client.get_secret(secret_name).value
            return secret_value

        except Exception as err:
            logger.error(f"Failed to get secret '{secret_name}': {err}")
            raise

    def _log_config(self) -> None:
        """Log configuration values with sensitive data redacted."""
        logger.info("Application configuration:")

        redacted = self.eventhub_connection_string[:20] + "..."
        logger.info(f"  EVENTHUB_CONNECTION_STRING: {redacted}")

        if self.eventhub_namespace:
            logger.info(f"  EVENTHUB_NAMESPACE: {self.eventhub_namespace}")

        logger.info(f"  EVENTHUB_NAME: {self.eventhub_name}")
        logger.info(f"  STORAGE_ACCOUNT_NAME: {self.storage_account_name}")
        logger.info(f"  STORAGE_CONTAINER: {self.storage_container}")
        logger.info(f"  NUM_SENSORS: {self.num_sensors}")
        logger.info(f"  SIMULATION_INTERVAL_MS: {self.simulation_interval_ms}")
        logger.info(f"  SENSOR_DATA_FILE: {self.data_file}")


config = Config()
