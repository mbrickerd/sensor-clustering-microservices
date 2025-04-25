"""
Main entry point for the ML Prediction Service.

This module initialises and runs the inference service that processes
sensor readings, loads clustering models from MLflow, makes predictions,
and detects data drift. It handles database connection setup,
predictor service initialisation, and graceful shutdown.
"""

import asyncio
import time

from loguru import logger

from domain.models import init_db
from predictor.config import config
from predictor.services.predictor import PredictorService


async def main() -> None:
    """
    Main entry point for the inference service.

    This function performs the following operations:
    1. Waits for services (PostgreSQL, MLflow) to be ready
    2. Initialises the database connection
    3. Creates and starts the prediction service
    4. Handles exceptions and provides graceful shutdown

    Returns:
        `None`
    """
    logger.info("Waiting for services to be ready...")
    time.sleep(60)

    logger.info("Initialising database connection...")
    db_url = config.get_postgres_uri()
    await init_db(db_url)

    logger.info("Database initialised successfully.")
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
