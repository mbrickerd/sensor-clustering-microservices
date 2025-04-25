"""
Main entry point for the Sensor Data Producer Service.

This module initialises and runs the producer service that simulates
machine sensor readings and publishes them to Kafka. It handles the
initial wait for Kafka to be ready and starts the continuous simulation
process.
"""

import time

from loguru import logger

from producer.services import SensorDataProducer

if __name__ == "__main__":
    time.sleep(10)
    logger.info("Starting sensor data producer...")

    producer = SensorDataProducer()
    producer.produce_messages()
