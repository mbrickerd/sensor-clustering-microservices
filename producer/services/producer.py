"""
Sensor data producer implementation for the Sensor Data Producer Service.

This module provides the main implementation of the sensor data simulator
that generates realistic machine sensor readings and publishes them to Kafka.
It simulates both normal machine operation and failure conditions based on
statistical models derived from reference data.
"""

import json
import random
import time
from datetime import datetime
from typing import Any, TypedDict
from uuid import uuid4

from kafka import KafkaProducer
from loguru import logger

from producer.config import config
from producer.models import FailureInfo, SensorMessage, SensorReading
from producer.utils.analysis import analyse_dataset


class MachineState(TypedDict):
    """
    Type definition for tracking machine state during simulation.

    This class defines the structure of the machine state dictionary that
    tracks the current values of all sensors, active failure information,
    and timing data for the simulation.

    Attributes:
        `active_failure`: Current failure information or `None` if no active failure
        `current_values`: Dictionary mapping sensor names to their current values
        `time`: Current time counter for active failures
        `duration`: Total duration of the active failure
    """

    active_failure: FailureInfo | None
    current_values: dict[str, float]
    time: float | None
    duration: float | None


class SensorDataProducer:
    """
    Service for generating and publishing simulated sensor data to Kafka.

    This class is responsible for simulating realistic sensor readings from
    industrial machines, including both normal operation and failure conditions.
    It uses statistical properties derived from reference data to generate
    values that mimic real-world behavior, and publishes these readings to
    Kafka in a consistent format.

    The simulation includes random drift, mean-reversion, and the ability to
    simulate different types of failures with specific sensor signatures.

    Attributes:
        `sensor_stats`: Statistical properties of each sensor during normal operation
        `failure_patterns`: Patterns of sensor behavior during different failure types
        `producer`: KafkaProducer instance for publishing messages
        `machine_id`: Unique identifier for the simulated machine
        `machine`: Current state of the simulated machine
    """

    def __init__(self) -> None:
        """
        Initialise the producer with data analysis.

        Analyses reference data to extract statistical properties of sensors
        during normal operation and failure conditions. Initialises the Kafka
        producer connection and creates a simulated machine with random initial
        sensor values.

        Returns:
            `None`
        """
        self.sensor_stats, self.failure_patterns = analyse_dataset(
            config.data_file,
            config.num_sensors,
        )

        self.producer = KafkaProducer(
            bootstrap_servers=config.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        self.machine_id = str(uuid4())[:8]
        self.machine: MachineState = {
            "active_failure": None,
            "current_values": self.generate_initial_values(),
            "time": None,
            "duration": None,
        }

        logger.info("Producer initialised with 1 machine")
        logger.info(f"Connected to Kafka at {config.kafka_bootstrap_servers}")

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
        values = {}
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
        current_values = self.machine["current_values"]
        readings = {}

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
            failure = self.machine["active_failure"]
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

        elif random.random() < 0.05:
            self.machine["active_failure"] = FailureInfo(
                time=0,
                duration=random.randint(30, 60),
            )
            logger.info(f"Failure started on {self.machine_id}")

        return {"readings": readings, "has_failure": has_failure}

    def produce_messages(self) -> None:
        """
        Continuously produce and publish sensor messages to Kafka.

        Enters a loop that simulates sensor readings, formats them into
        messages, and publishes them to the configured Kafka topic. The
        loop continues until interrupted by a keyboard interrupt or an
        exception occurs. Handles cleanup of Kafka producer resources
        upon exit.

        Returns:
            `None`
        """
        try:
            while True:
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

                self.producer.send(config.kafka_topic, message.model_dump())
                self.producer.flush()

                if sensor_data["has_failure"]:
                    logger.debug("Sent message with failure indication")

                time.sleep(config.simulation_interval_ms / 1000)

        except KeyboardInterrupt:
            logger.info("Producer stopped by user")

        except Exception as err:
            logger.error(f"Error in producer: {str(err)}")

        finally:
            self.producer.close()
