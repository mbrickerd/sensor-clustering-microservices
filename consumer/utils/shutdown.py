"""
Signal handling and shutdown utilities for the Sensor Data Consumer Service.

This module provides functions for graceful shutdown of the consumer
service when it receives termination signals (`SIGINT`, `SIGTERM`).
"""

import asyncio
import signal
from asyncio import AbstractEventLoop
from signal import Signals
from typing import Callable

from loguru import logger

from consumer.services.consumer import SensorDataConsumer


async def shutdown(
    signal: Signals, loop: AbstractEventLoop, consumer: SensorDataConsumer
) -> None:
    """
    Shutdown handler for graceful termination.

    This function is called when the application receives a termination
    signal (`SIGINT` or `SIGTERM`). It stops the Kafka consumer, cancels
    all pending tasks, and stops the event loop.

    Args:
        signal (`Signals`): The signal that triggered the shutdown
        loop (`AbstractEventLoop`): The asyncio event loop
        consumer (`SensorDataConsumer`): The Kafka consumer to stop

    Returns:
        `None`
    """
    logger.info(f"Received exit signal {signal.name}...")
    await consumer.stop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


def create_signal_handler(
    s: Signals, loop: AbstractEventLoop, consumer: SensorDataConsumer
) -> Callable[[], asyncio.Task[None]]:
    """
    Create a handler function for a specific termination signal.

    Creates a callable that will initiate the shutdown process when invoked.
    This function is used to register handlers for termination signals like
    SIGINT and SIGTERM.

    Args:
        s (`Signals`): The signal to handle
        loop (`AbstractEventLoop`): The asyncio event loop to stop
        consumer (`SensorDataConsumer`): The Kafka consumer to stop

    Returns:
        `Callable[[], asyncio.Task[None]]`: A function that creates and returns a shutdown task
    """
    return lambda: asyncio.create_task(shutdown(s, loop, consumer))


async def setup_signal_handlers(
    loop: AbstractEventLoop, consumer: SensorDataConsumer
) -> None:
    """
    Set up signal handlers for graceful shutdown.

    Registers signal handlers for `SIGINT` and `SIGTERM` that will trigger
    the `shutdown` function when received. This ensures graceful shutdown
    of the application when it's terminated.

    Args:
        loop (`AbstractEventLoop`): The asyncio event loop
        consumer (`SensorDataConsumer`): The Kafka consumer to be stopped on shutdown

    Returns:
        `None`
    """
    for sig in (signal.SIGINT, signal.SIGTERM):
        handler = create_signal_handler(sig, loop, consumer)
        loop.add_signal_handler(sig, handler)
