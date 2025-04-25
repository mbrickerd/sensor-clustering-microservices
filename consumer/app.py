"""
Main entry point for the Sensor Data Consumer Service.

This module initialises and runs the Kafka consumer that processes
sensor data messages and stores them in PostgreSQL. It handles
database connection setup, consumer initialisation, and signal
handling for graceful shutdowns.
"""

import asyncio
import time

from loguru import logger

from consumer.config import config
from consumer.services import SensorDataConsumer
from consumer.utils import setup_signal_handlers
from domain.models import init_db


async def main():
    """
    Main entry point for the consumer application.

    This function performs the following operations:
    1. Waits for Kafka and PostgreSQL services to be ready
    2. Initialises the database connection
    3. Creates and starts the sensor data consumer
    4. Sets up signal handlers for graceful shutdown

    Returns:
        `None`
    """
    logger.info("Waiting for services to be ready...")
    time.sleep(10)

    logger.info("Initialising database connection...")
    db_url = config.get_postgres_uri()
    await init_db(db_url)
    logger.info("Database initialised successfully.")

    consumer = SensorDataConsumer()

    loop = asyncio.get_event_loop()
    await setup_signal_handlers(loop, consumer)

    try:
        logger.info("Starting sensor data consumer...")
        await consumer.start()

    finally:
        logger.info("Shutting down...")


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
