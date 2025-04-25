"""
Kafka consumer implementation for the Sensor Data Consumer Service.

This module contains the implementation of the Kafka consumer that
subscribes to sensor data topics, processes incoming messages, and
forwards them to the database service for storage.
"""

import json

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from loguru import logger

from consumer.config import config
from consumer.services import DatabaseService


class SensorDataConsumer:
    """
    Consumer for sensor data from Kafka.

    This class is responsible for consuming sensor data messages from
    a Kafka topic, deserializing the JSON content, and forwarding
    the data to the `DatabaseService` for processing and storage.

    It handles connection management, message processing, and error
    handling for the Kafka consumer.
    """

    def __init__(self) -> None:
        """
        Initialise the Kafka consumer.

        Creates a new `AIOKafkaConsumer` instance configured with the
        settings from the application's `Config` object. Sets up the
        consumer with the appropriate topic, bootstrap servers, and
        consumer group ID.

        Returns:
            `None`
        """
        self.consumer = AIOKafkaConsumer(
            config.kafka_topic,
            bootstrap_servers=config.kafka_bootstrap_servers,
            group_id=config.kafka_group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            auto_commit_interval_ms=config.commit_interval_ms,
        )
        self.db = DatabaseService()
        self.running = False

    async def start(self) -> None:
        """
        Start the consumer.

        Begins consuming messages from the configured Kafka topic and
        processes each message by deserializing it and forwarding it
        to the database service. Handles JSON decoding errors and other
        exceptions that may occur during message processing.

        The consumer runs in a continuous loop until stopped or until
        an unrecoverable error occurs.

        Returns:
            `None`

        Raises:
            `KafkaError`: If there's an issue with the Kafka connection
        """
        logger.info(f"Starting consumer for topic: {config.kafka_topic}")
        await self.consumer.start()
        self.running = True

        try:
            async for message in self.consumer:
                try:
                    value = json.loads(message.value.decode("utf-8"))
                    logger.debug(
                        f"Received message from partition {message.partition}, "
                        f" offset {message.offset}"
                    )
                    await self.db.process_message(value)

                except json.JSONDecodeError:
                    logger.error(f"Failed to parse message as JSON: {message.value}")

                except Exception as err:
                    logger.error(f"Error processing message: {str(err)}")

        except KafkaError as err:
            logger.error(f"Kafka error: {str(err)}")

        finally:
            await self.stop()

    async def stop(self) -> None:
        """
        Stop the consumer.

        Gracefully stops the Kafka consumer if it is currently running.
        This method is typically called during application shutdown or
        when an unrecoverable error occurs.

        Returns:
            `None`
        """
        if self.running:
            logger.info("Stopping consumer...")
            await self.consumer.stop()
            self.running = False
