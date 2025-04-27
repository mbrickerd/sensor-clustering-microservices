"""
Database service for the Sensor Data Consumer Service.

This module provides the DatabaseService class that processes messages
from the Kafka consumer and stores them in PostgreSQL. It handles machine
registration, failure detection and tracking, and sensor reading storage.
"""

from datetime import datetime
from typing import Any, cast

from loguru import logger
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction

from domain.models import Failure, Machine, SensorReading


class DatabaseService:
    """
    Service class for database operations.

    This class is responsible for processing and storing sensor data
    received from Kafka. It manages machine registration, tracks
    failure events, and stores sensor readings in the database.
    """

    @staticmethod
    async def get_or_create_machine(machine_id: str) -> Machine:
        """
        Get an existing machine or create a new one.

        Attempts to retrieve a machine with the specified ID from the
        database. If the machine exists, the `last_seen` timestamp is
        updated. If the machine does not exist, a new machine record
        is created.

        Args:
            machine_id (`str`): Unique identifier for the machine

        Returns:
            `Machine`: Retrieved or newly created `Machine` instance

        Raises:
            `Exception`: If database operations fail
        """
        try:
            machine = await Machine.get(machine_id=machine_id)
            machine.last_seen = datetime.now()
            await machine.save()
            return cast(Machine, machine)

        except DoesNotExist:
            logger.info(f"Creating new machine: {machine_id}")
            return cast(Machine, await Machine.create(machine_id=machine_id))

    @staticmethod
    async def get_active_failure(machine: Machine) -> Failure | None:
        """
        Get the active failure for this machine.

        Queries the database for any active failure associated with the
        specified machine. An active failure is one where `is_active=True`.

        Args:
            machine (`Machine`): The machine to check for active failures

        Returns:
            `Failure | None`: The active failure if one exists, otherwise `None`

        Raises:
            `Exception`: If database operations fail
        """
        try:
            failure = await Failure.get(machine=machine, is_active=True)
            return cast(Failure, failure)

        except DoesNotExist:
            return None

    @classmethod
    async def process_message(cls, message_data: dict[str, Any]) -> None:
        """
        Process a Kafka message and store it in the database.

        Extracts information from the message, creates or updates machine
        records, detects and tracks failure events, and stores sensor
        readings in the database. All database operations are performed
        within a transaction for consistency.

        Args:
            message_data (`dict[str, Any]`): Deserialized message data from Kafka

        Returns:
            `None`

        Raises:
            `Exception`: If message processing or database operations fail
        """
        try:
            machine_id = message_data.get("machine_id")
            timestamp_str = message_data.get("timestamp")
            readings_data = message_data.get("readings", {})

            if not machine_id or not timestamp_str:
                logger.warning(f"Incomplete message data: {message_data}")
                return

            timestamp = datetime.fromisoformat(timestamp_str)
            sensor_values = readings_data.get("readings", {})
            has_failure = readings_data.get("has_failure", False)

            async with in_transaction():
                machine = await cls.get_or_create_machine(machine_id)
                failure = None

                if has_failure:
                    failure = await cls.get_active_failure(machine)

                    if not failure:
                        failure = await Failure.create(
                            machine=machine,
                            start_time=timestamp,
                        )
                        failure = cast(Failure, failure)
                        logger.info(f"New failure detected on machine {machine_id}")

                elif not has_failure:
                    active_failures = await Failure.filter(
                        machine=machine, is_active=True
                    )
                    for active_failure in active_failures:
                        active_failure.is_active = False
                        active_failure.end_time = timestamp
                        await active_failure.save()
                        logger.info(f"Failure resolved on machine {machine_id}")

                await SensorReading.create(
                    machine=machine,
                    timestamp=timestamp,
                    values=sensor_values,
                    failure=failure,
                )

        except Exception as err:
            logger.error(f"Error processing message: {str(err)}")
            raise
