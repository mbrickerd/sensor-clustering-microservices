import json

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from loguru import logger

from consumer.config import config
from consumer.services.database import DatabaseService


class SensorDataConsumer:
    """Consumer for sensor data from Kafka."""

    def __init__(self) -> None:
        """Initialize the Kafka consumer."""
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
        """Start the consumer."""
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
        """Stop the consumer."""
        if self.running:
            logger.info("Stopping consumer...")
            await self.consumer.stop()
            self.running = False
