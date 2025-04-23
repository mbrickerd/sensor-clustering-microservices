import asyncio
import time
from loguru import logger

from consumer.config import config
from domain.models import init_db
from consumer.services.consumer import SensorDataConsumer
from consumer.utils.shutdown import setup_signal_handlers


# TODO: add dependency in docker compose
async def main():
    """Main entry point for the consumer application."""
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