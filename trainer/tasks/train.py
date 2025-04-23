import asyncio
from trainer.celery import celery
from trainer.services.trainer import TrainerService
from loguru import logger


async def run():
    """Run the training job asynchronously"""
    trainer = TrainerService()
    await trainer.run()
    return "success"


@celery.task(bind=True)
def train_model(self):
    """Celery task to train a model"""
    task_id = self.request.id
    logger.info(f"Starting training task {task_id}")
    
    try:
        result = asyncio.run(run())
        logger.info(f"Training task {task_id} completed successfully")
        return {"status": "completed", "result": result}
        
    except Exception as err:
        logger.error(f"Training task {task_id} failed: {str(err)}")
        return {"status": "failed", "error": str(err)}