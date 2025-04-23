from fastapi import FastAPI
import uvicorn
import asyncio
import sys
import os
from loguru import logger
from trainer.api.routes import health, train
from trainer.services.trainer import TrainerService


app = FastAPI(
    title="Sensor Trainer API",
    description="API for training machine learning models for sensor data",
    version="1.0.0",
)

app.include_router(health, prefix="/api", tags=["health"])
app.include_router(train, prefix="/api", tags=["train"])


async def run():
    """Run the trainer directly"""
    logger.info("Starting ML training service")
    trainer = TrainerService()
    await trainer.run()
    logger.info("ML training service completed")
    

if __name__ == "__main__":
    api_mode = os.environ.get("API_MODE", "false").lower() == "true"
    
    if api_mode:
        uvicorn.run("trainer.app:app", host="0.0.0.0", port=8000, workers=1)
        logger.info("ML training service started in API mode")
        
    else:
        try:
            asyncio.run(run())
            logger.info("ML training service completed")
            
        except KeyboardInterrupt:
            logger.info("ML training service stopped by user")
            
        except Exception as err:
            logger.error(f"ML training service failed: {str(err)}")
            sys.exit(1)