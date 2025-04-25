# Producer Service

This directory contains the sensor data producer service for the Sensor Failure Detection System. This service simulates machine sensor readings and publishes them to Kafka for consumption by other components.

**Table of contents**
- [Producer Service](#producer-service)
  - [Overview](#overview)
  - [Directory Structure](#directory-structure)
  - [Dockerfile Explanation](#dockerfile-explanation)
  - [Environment Variables](#environment-variables)
  - [Key Components](#key-components)
  - [Data Simulation](#data-simulation)
  - [Failure Simulation](#failure-simulation)
  - [Integration with Microservices](#integration-with-microservices)
  - [Troubleshooting](#troubleshooting)

## Overview

The producer service is responsible for generating realistic simulated sensor data:
- Generates sensor readings that mimic real machine behavior
- Simulates random failures with specific patterns
- Publishes messages to Kafka in a consistent format
- Supports configuration of number of sensors and simulation speed
- Provides a controllable data source for testing and development

## Directory Structure

```
producer/
├── Dockerfile                 # Multi-stage Docker build
├── README.md                  # This documentation file
├── __init__.py
├── app.py                     # Main application entry point
├── config.py                  # Configuration from environment variables
├── models/
│   ├── __init__.py
│   ├── failure.py             # Failure data models
│   ├── message.py             # Kafka message models
│   └── reading.py             # Sensor reading models
├── pyproject.toml             # Project dependencies
├── services/
│   ├── __init__.py
│   └── producer.py            # Main producer implementation
└── utils/
    ├── __init__.py
    └── analysis.py            # Data analysis utilities
```

## Dockerfile Explanation

The Dockerfile uses a multi-stage build to optimise the image size:

```dockerfile
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY domain/pyproject.toml domain/
COPY producer/pyproject.toml producer/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir uv && \
    cd domain && uv pip install --system -e . && \
    cd ../producer && uv pip install --system -e .

COPY domain/ /app/domain/
COPY producer/ /app/producer/

FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/domain ./domain
COPY --from=builder /app/producer ./producer
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENV PYTHONPATH=/app

CMD ["python", "-m", "producer.app"]
```

Key aspects:
- Uses Python 3.10 slim image for both build and runtime stages
- Utilises multi-stage build to minimise image size
- Employs `uv` for faster dependency installation
- Mounts cache to speed up rebuilds
- Includes curl for healthchecks

## Environment Variables

| Environment Variable | Description | Default | Required |
| -------------------- | ----------- | ------- | -------- |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | localhost:9092 | Yes |
| `KAFKA_TOPIC` | Topic to publish messages to | sensor-data | Yes |
| `NUM_SENSORS` | Number of sensors to simulate | 20 | No |
| `SIMULATION_INTERVAL_MS` | Delay between messages (milliseconds) | 1000 | No |
| `SENSOR_DATA_FILE` | Path to CSV with sensor pattern data | data_sensors.csv | Yes |

## Key Components

The producer service consists of these main components:

1. **Sensor Data Producer (`producer.py`)**
   - Main service that generates and publishes sensor readings
   - Manages sensor values and failure simulation
   - Publishes messages to Kafka

2. **Data Analysis Tools (`analysis.py`)**
   - Analyses reference CSV data to extract sensor patterns
   - Calculates statistical properties for normal behavior
   - Identifies failure patterns from labeled data
   - Provides default values when CSV data is unavailable

3. **Configuration (`config.py`)**
   - Centralises configuration from environment variables
   - Provides defaults for development environments
   - Logs configuration for debugging

## Data Simulation

The data simulation process follows these steps:

1. **Initialisation**
   - Load reference data from CSV file
   - Extract normal sensor statistics (mean, standard deviation, etc.)
   - Extract failure patterns from labeled data
   - Initialise Kafka producer connection
   - Generate initial random sensor values based on statistics

2. **Data Generation**
   - Generate realistic sensor values with random drift
   - Apply mean-reversion to keep values within realistic ranges
   - Simulate failures based on probability and patterns
   - Format data into consistent message structure
   - Publish messages at configured intervals

3. **Statistical Properties**
   - Values follow normal distributions based on learned parameters
   - Random drift uses smaller standard deviation for realistic changes
   - Mean-reversion ensures long-term stability around expected values
   - Values are bounded to prevent unrealistic extremes

## Failure Simulation

The service simulates realistic machine failures:

- Random failures occur with 5% probability per cycle
- Failures have random durations (30-60 cycles)
- During failures, sensor values gradually shift toward failure patterns
- Progress increases linearly from 0% to 100% over 10 cycles
- Failure patterns are derived from labeled reference data
- Multiple failure types with different sensor signatures are supported
- Failures are flagged in the message metadata for ground truth

## Integration with Microservices

The producer service interacts with these components:

1. **Kafka**
   - Publishes sensor reading messages
   - Uses JSON serialization for compatibility
   - Messages include machine ID, timestamp, and readings

2. **Consumer Service**
   - Reads messages produced by this service
   - Stores readings in the database
   - Identifies failures for model training

3. **CSV Data File**
   - Optional reference data for realistic patterns
   - Provides statistical parameters for simulation
   - Can include labeled failure data to learn patterns

The message format is:
```json
{
  "machine_id": "12345678",
  "timestamp": "2025-04-25T12:34:56.789",
  "readings": {
    "readings": {
      "Sensor 1": 0.45,
      "Sensor 2": -0.12,
      ...
    },
    "has_failure": false
  }
}
```

## Troubleshooting

Common issues and their solutions:

1. **Kafka Connection Issues**
   - Verify Kafka is running: `docker ps | grep kafka`
   - Check bootstrap server configuration
   - Try connecting with `kafkacat` for debugging
   - Verify network connectivity between containers

2. **CSV Data File Issues**
   - Ensure file exists at the specified path
   - Verify file has the expected format with sensor columns
   - Check that volume mount is correct in docker-compose
   - Note that default values will be used if file is missing

3. **Performance Issues**
   - Adjust `SIMULATION_INTERVAL_MS` to control message rate
   - Monitor Kafka broker performance
   - Check for consumer lag if message processing is slow
   - Consider adjusting `buffer.memory` in Kafka configuration

4. **Container Startup Issues**
   - The container waits 10 seconds for Kafka to be ready
   - Check logs with `docker logs sensor-producer`
   - Verify that Kafka's healthcheck is passing
   - Try increasing the startup delay if necessary
