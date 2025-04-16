import json
import random
import time
from datetime import datetime
from loguru import logger
from kafka import KafkaProducer
from utils import analyse_dataset
from config import config


class SensorDataProducer:
    def __init__(self) -> None:
        """Initialize the producer with data analysis"""
        self.sensor_stats, self.failure_patterns = analyse_dataset(
            config.data_file,
            config.num_sensors,
        )

        # Connect to Kafka
        self.producer = KafkaProducer(
            bootstrap_servers=config.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        # Initialise machine states
        self.machines = {}
        for i in range(config.num_machines):
            self.machines[f"machine-{i+1}"] = {
                "active_failure": None,
                "current_values": self.generate_initial_values(),
            }

        logger.info(f"Producer initialised with {config.num_machines} machines")
        logger.info(f"Connected to Kafka at {config.kafka_bootstrap_servers}")

    def generate_initial_values(self):
        """Generate initial sensor values based on statistical properties"""
        values = {}
        for i in range(config.num_sensors):
            col = f"Sensor {i}"
            stats = self.sensor_stats.get(col, {"mean": 0, "std": 1})
            values[col] = random.normalvariate(stats["mean"], stats["std"])

        return values

    def update_sensor_values(self, machine_id):
        """Update sensor values with random walk and apply failures if active"""
        machine = self.machines[machine_id]
        current_values = machine["current_values"]
        readings = {}

        # Update each sensor value with random walk
        for i in range(config.num_sensors):
            col = f"Sensor {i}"
            stats = self.sensor_stats.get(
                col, {"mean": 0, "std": 1, "min": -1, "max": 1}
            )

            # Current value plus small random change
            drift = stats["std"] * 0.1
            new_value = current_values[col] + random.normalvariate(0, drift)

            # Pull back toward mean (mean reversion)
            mean_reversion = 0.05 * (stats["mean"] - new_value)
            new_value += mean_reversion

            # Apply bounds
            new_value = max(min(new_value, stats["max"] * 1.2), stats["min"] * 1.2)

            # Store updated value
            current_values[col] = new_value
            readings[col] = round(new_value, 6)

        # Apply failure pattern if active
        if machine["active_failure"]:
            failure = machine["active_failure"]
            pattern = self.failure_patterns.get(failure["type"])

            if pattern:
                # Apply failure pattern with increasing intensity
                progress = min(1.0, failure["time"] / 10)

                for col, stats in pattern.items():
                    if col in readings:
                        # Generate value from failure distribution
                        failure_value = random.normalvariate(
                            stats["mean"], stats["std"]
                        )

                        # Blend normal and failure values based on progression
                        readings[col] = round(
                            readings[col] * (1 - progress) + failure_value * progress, 6
                        )

            # Update failure time
            failure["time"] += 1

            # Check if failure should end
            if failure["time"] >= failure["duration"]:
                machine["active_failure"] = None
                logger.info(f"Failure resolved on {machine_id}")

        # Randomly trigger new failures (0.5% chance per update)
        elif random.random() < 0.005:
            failure_types = list(self.failure_patterns.keys())
            failure_type = random.choice(failure_types)

            machine["active_failure"] = {
                "type": failure_type,
                "time": 0,
                "duration": random.randint(20, 50),  # Last 20-50 cycles
            }
            logger.info(f"Failure type {failure_type} started on {machine_id}")

        return readings, machine["active_failure"]

    def produce_messages(self):
        """Main loop to produce continuous stream of sensor data"""
        try:
            while True:
                for machine_id in self.machines:
                    # Update sensor values
                    readings, active_failure = self.update_sensor_values(machine_id)

                    # Create message
                    message = {
                        "machine_id": machine_id,
                        "timestamp": datetime.now().isoformat(),
                        "readings": readings,
                        "has_failure": active_failure is not None,
                    }

                    # Add failure info if present
                    if active_failure:
                        message["failure_type"] = str(active_failure["type"])

                    # Send to Kafka
                    self.producer.send(config.kafka_topic, message)

                # Flush and sleep
                self.producer.flush()
                time.sleep(config.simulation_interval_ms / 1000)

        except KeyboardInterrupt:
            logger.info("Producer stopped by user")
        except Exception as err:
            logger.error(f"Error in producer: {str(err)}")
        finally:
            self.producer.close()
