from loguru import logger
import asyncio
from asyncio import AbstractEventLoop
import signal
from signal import Signals

from consumer.services.consumer import SensorDataConsumer


async def shutdown(signal: Signals, loop: AbstractEventLoop, consumer: SensorDataConsumer) -> None:
    """Shutdown handler for graceful termination."""
    logger.info(f"Received exit signal {signal.name}...")
    await consumer.stop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
        
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


async def setup_signal_handlers(loop: AbstractEventLoop, consumer: SensorDataConsumer) -> None:
    """Set up signal handlers for graceful shutdown."""
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s, loop, consumer))
        )