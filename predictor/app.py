import asyncio
import time
from loguru import logger

from domain.models import init_db
from predictor.config import config
from predictor.services.predictor import PredictorService


async def main():
    """Main entry point for the inference service."""
    logger.info("Waiting for services to be ready...")
    time.sleep(10)
    
    logger.info("Initializing database connection...")
    db_url = config.get_postgres_uri()
    await init_db(db_url)
    logger.info("Database initialized successfully.")
    
    prediction_service = PredictorService()
    
    try:
        logger.info("Starting inference service...")
        await prediction_service.run()
        
    except Exception as err:
        logger.error(f"Error in inference service: {err}")
        
    finally:
        logger.info("Shutting down inference service...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("Inference service stopped by user")
        
    except Exception as err:
        logger.error(f"Unhandled exception: {err}")
        exit(1)