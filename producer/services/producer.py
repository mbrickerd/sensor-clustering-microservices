import json
import random
import time
from typing import Any
from uuid import uuid4
from datetime import datetime
from loguru import logger
from kafka import KafkaProducer
from producer.utils.analysis import analyse_dataset
from producer.config import config
from producer.models import FailureInfo, SensorReading, SensorMessage


class SensorDataProducer:
    def __init__(self) -> None:
        """Initialize the producer with data analysis"""
        self.sensor_stats, self.failure_patterns = analyse_dataset(
            config.data_file,
            config.num_sensors,
        )

        self.producer = KafkaProducer(
            bootstrap_servers=config.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        self.machine_id = str(uuid4())[:8]
        self.machine = {
            "active_failure": None,
            "current_values": self.generate_initial_values(),
        }
        
        logger.info("Producer initialised with 1 machine")
        logger.info(f"Connected to Kafka at {config.kafka_bootstrap_servers}")

    def generate_initial_values(self) -> dict[str, float]:
        """Generate initial sensor values based on statistical properties"""
        values = {}
        for i in range(1, config.num_sensors + 1):
            col = f"Sensor {i}"
            stats = self.sensor_stats.get(col, {"mean": 0, "std": 1})
            values[col] = random.normalvariate(stats["mean"], stats["std"])

        return values

    def update_sensor_values(self) -> dict[str, Any]:
        """Update sensor values and return readings with implicit failures"""
        current_values = self.machine["current_values"]
        readings = {}
        
        has_failure = self.machine["active_failure"] is not None
        
        # Generate normal readings with random drift
        for i in range(1, config.num_sensors + 1):
            col = f"Sensor {i}"
            stats = self.sensor_stats.get(col, {"mean": 0, "std": 1, "min": -1, "max": 1})
            drift = stats["std"] * 0.1
            new_value = current_values.get(col, stats["mean"]) + random.normalvariate(0, drift)
            mean_reversion = 0.05 * (stats["mean"] - new_value)
            new_value += mean_reversion
            new_value = max(min(new_value, stats["max"] * 1.2), stats["min"] * 1.2)
            current_values[col] = new_value
            readings[col] = round(new_value, 6)
        
        if self.machine["active_failure"]:
            failure = self.machine["active_failure"]
            pattern = random.choice(list(self.failure_patterns.values()))
            progress = min(1.0, failure.time / 10)
            for col, stats in pattern.items():
                if col in readings:
                    failure_value = random.normalvariate(stats["mean"], stats["std"])
                    readings[col] = round(readings[col] * (1 - progress) + failure_value * progress, 6)
            
            failure.time += 1
            if failure.time >= failure.duration:
                self.machine["active_failure"] = None
                logger.info(f"Failure resolved on Machine {self.machine_id}")
                    
        elif random.random() < 0.05:
            self.machine["active_failure"] = FailureInfo(
                time=0,
                duration=random.randint(30, 60),
            )
            logger.info(f"Failure started on {self.machine_id}")

        return {
            "readings": readings,
            "has_failure": has_failure
        }

    def produce_messages(self) -> None:
        try:
            while True:
                sensor_data = self.update_sensor_values()
                sensor_reading = SensorReading(
                    readings=sensor_data["readings"],
                    has_failure=sensor_data["has_failure"]
                )
                
                message = SensorMessage(
                    machine_id=self.machine_id,
                    timestamp=datetime.now().isoformat(),
                    readings=sensor_reading
                )
                
                self.producer.send(config.kafka_topic, message.model_dump())
                self.producer.flush()
                
                if sensor_data["has_failure"]:
                    logger.debug(f"Sent message with failure indication")
                
                time.sleep(config.simulation_interval_ms / 1000)
                
        except KeyboardInterrupt:
            logger.info("Producer stopped by user")
            
        except Exception as err:
            logger.error(f"Error in producer: {str(err)}")
            
        finally:
            self.producer.close()