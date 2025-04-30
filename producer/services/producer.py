"""
Sensor data producer implementation for the Sensor Data Producer Service.

This module provides the main implementation of the sensor data simulator
that generates realistic machine sensor readings and publishes them to Azure
Event Hubs. It simulates both normal machine operation and failure conditions
based on statistical models derived from reference data.
"""

import json
import random
import time
from datetime import datetime
from typing import Any, cast
from uuid import uuid4

from azure.eventhub import EventData, EventHubProducerClient
from azure.identity import DefaultAzureCredential
from loguru import logger

from producer.config import config
from producer.models import FailureInfo, SensorMessage, SensorReading
from producer.services.health import HealthService
from producer.services.storage import StorageService
from producer.utils import analyse_dataset


class SensorDataProducer:
    """
    Service for generating and publishing simulated sensor data to Azure Event Hubs.

    This class is responsible for simulating realistic sensor readings from
    industrial machines, including both normal operation and failure conditions.
    It uses statistical properties derived from reference data to generate
    values that mimic real-world behavior, and publishes these readings to
    Event Hubs in a consistent format.

    The simulation includes random drift, mean-reversion, and the ability to
    simulate different types of failures with specific sensor signatures.

    Attributes:
        `sensor_stats`: Statistical properties of each sensor during normal operation
        `failure_patterns`: Patterns of sensor behavior during different failure types
        `producer_client`: EventHubProducerClient instance for publishing messages
        `machine_id`: Unique identifier for the simulated machine
        `machine`: Current state of the simulated machine
        `health_service`: Optional health service for monitoring and metrics
    """

    def __init__(self) -> None:
        """
        Initialise the producer with data analysis.

        Analyses reference data to extract statistical properties of sensors
        during normal operation and failure conditions. Initialises the Event Hubs
        producer connection and creates a simulated machine with random initial
        sensor values.

        Returns:
            `None`
        """
        # Initialize empty dictionaries first to avoid redefining attributes
        self.sensor_stats: dict[str, dict[str, Any]] = {}
        self.failure_patterns: dict[str, dict[str, Any]] = {}

        storage_service = StorageService(
            user_id="sensor-producer",
            container_name=config.storage_container,
            account_name=config.storage_account_name,
        )

        try:
            file_content = storage_service.read_blob(config.data_file, binary=False)
            # Fix type compatibility issue by explicitly casting to str
            if isinstance(file_content, str):
                # Use type casting to ensure proper type assignment
                analysis_result = analyse_dataset(
                    file_content,
                    config.num_sensors,
                )
                # Cast the result to the expected types
                self.sensor_stats = cast(dict[str, dict[str, Any]], analysis_result[0])
                self.failure_patterns = cast(
                    dict[str, dict[str, Any]], analysis_result[1]
                )
            else:
                # Handle the case when file_content is bytes
                logger.warning(
                    "File content is not in string format. Using empty data."
                )

        except Exception as err:
            logger.error(f"Failed to read or analyse data file: {err}")

        if config.eventhub_connection_string:
            self.producer_client = EventHubProducerClient.from_connection_string(
                conn_str=config.eventhub_connection_string,
                eventhub_name=config.eventhub_name,
            )

        else:
            credential = DefaultAzureCredential()
            self.producer_client = EventHubProducerClient(
                fully_qualified_namespace=f"{config.eventhub_namespace}.servicebus.windows.net",
                eventhub_name=config.eventhub_name,
                credential=credential,
            )

        self.machine_id = str(uuid4())[:8]
        self.machine: dict[str, Any] = {
            "active_failure": None,
            "current_values": self.generate_initial_values(),
            "time": None,
            "duration": None,
        }

        self.health_service = HealthService()

        logger.info("Producer initialised with 1 machine")
        logger.info(f"Connected to Event Hub: {config.eventhub_name}")

    def check_health(self) -> bool:
        """
        Check the health of the producer service.

        Verifies that the Event Hubs client is still functional.

        Returns:
            `bool`: True if the service is healthy, False otherwise
        """
        try:
            return self.producer_client is not None and not getattr(
                self.producer_client, "_closed", False
            )

        except Exception as err:
            logger.error(f"Health check failed: {err}")
            return False

    def generate_initial_values(self) -> dict[str, float]:
        """
        Generate initial sensor values based on statistical properties.

        Creates a set of initial values for all sensors based on their
        statistical properties (mean and standard deviation) from the
        reference data. Values are drawn from normal distributions to
        ensure realistic starting points.

        Returns:
            `dict[str, float]`: Dictionary mapping sensor names to their initial values
        """
        values: dict[str, float] = {}
        for i in range(1, config.num_sensors + 1):
            col = f"Sensor {i}"
            stats = self.sensor_stats.get(col, {"mean": 0, "std": 1})
            values[col] = random.normalvariate(stats["mean"], stats["std"])

        return values

    def update_sensor_values(self) -> dict[str, Any]:
        """
        Update sensor values and return readings with implicit failures.

        Simulates the evolution of sensor readings over time, including:
        - Random drift around mean values
        - Mean-reversion to maintain stability
        - Gradual progression of failure patterns when a failure is active
        - Random triggering of new failures
        - Resolution of active failures after their duration expires

        The method handles the entire simulation cycle for a single time step.

        Returns:
            `dict[str, Any]`: Dictionary containing the updated readings and
                failure indicator in the format:
                    {"readings": {sensor_name: value, ...},
                    "has_failure": bool}
        """
        current_values = cast(dict[str, float], self.machine["current_values"])
        readings: dict[str, float] = {}

        has_failure = self.machine["active_failure"] is not None

        for i in range(1, config.num_sensors + 1):
            col = f"Sensor {i}"
            stats = self.sensor_stats.get(
                col, {"mean": 0, "std": 1, "min": -1, "max": 1}
            )
            drift = stats["std"] * 0.1
            new_value = current_values.get(col, stats["mean"]) + random.normalvariate(
                0, drift
            )
            mean_reversion = 0.05 * (stats["mean"] - new_value)
            new_value += mean_reversion
            new_value = max(min(new_value, stats["max"] * 1.2), stats["min"] * 1.2)
            current_values[col] = new_value
            readings[col] = round(new_value, 6)

        if self.machine["active_failure"]:
            failure = cast(FailureInfo, self.machine["active_failure"])
            pattern = random.choice(list(self.failure_patterns.values()))
            progress = min(1.0, failure.time / 10)
            for col, stats in pattern.items():
                if col in readings:
                    failure_value = random.normalvariate(stats["mean"], stats["std"])
                    readings[col] = round(
                        readings[col] * (1 - progress) + failure_value * progress, 6
                    )

            failure.time += 1
            if failure.time >= failure.duration:
                self.machine["active_failure"] = None
                logger.info(f"Failure resolved on Machine {self.machine_id}")
                if self.health_service:
                    self.health_service.set_active_failures(0)

        elif random.random() < 0.05:
            self.machine["active_failure"] = FailureInfo(
                time=0,
                duration=random.randint(30, 60),
            )
            logger.info(f"Failure started on {self.machine_id}")
            if self.health_service:
                self.health_service.increment_failure_events()
                self.health_service.set_active_failures(1)

        return {"readings": readings, "has_failure": has_failure}

    def produce_messages(self) -> None:
        """
        Continuously produce and publish sensor messages to Azure Event Hubs.

        Enters a loop that simulates sensor readings, formats them into
        messages, and publishes them to the configured Event Hub. The
        loop continues until interrupted by a keyboard interrupt or an
        exception occurs. Handles cleanup of Event Hubs producer resources
        upon exit.

        Returns:
            `None`
        """
        try:
            while True:
                start_time = time.time()
                sensor_data = self.update_sensor_values()
                sensor_reading = SensorReading(
                    readings=sensor_data["readings"],
                    has_failure=sensor_data["has_failure"],
                )

                message = SensorMessage(
                    machine_id=self.machine_id,
                    timestamp=datetime.now().isoformat(),
                    readings=sensor_reading,
                )

                try:
                    event_data_batch = self.producer_client.create_batch()
                    serialized_message = json.dumps(message.model_dump()).encode(
                        "utf-8"
                    )
                    event_data_batch.add(EventData(serialized_message))

                    self.producer_client.send_batch(event_data_batch)

                    if self.health_service:
                        self.health_service.increment_messages_sent()
                        processing_time = time.time() - start_time
                        self.health_service.observe_processing_time(processing_time)

                except Exception as err:
                    logger.error(f"Error sending message: {str(err)}")
                    if self.health_service:
                        self.health_service.increment_message_errors()

                if sensor_data["has_failure"]:
                    logger.debug("Sent message with failure indication")

                time.sleep(config.simulation_interval_ms / 1000)

        except KeyboardInterrupt:
            logger.info("Producer stopped by user")

        except Exception as err:
            logger.error(f"Error in producer: {str(err)}")

        finally:
            self.producer_client.close()
