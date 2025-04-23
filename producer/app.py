import time

from loguru import logger

from producer.services.producer import SensorDataProducer

if __name__ == "__main__":
    # Wait for Kafka to be ready
    time.sleep(10)
    logger.info("Starting sensor data producer...")

    producer = SensorDataProducer()
    producer.produce_messages()
