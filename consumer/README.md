# Consumer Service

This directory contains the Kafka consumer service for the Sensor Failure Detection System. This service is responsible for consuming sensor data messages from Kafka and storing them in PostgreSQL.

**Table of contents**
- [Consumer Service](#consumer-service)
  - [Overview](#overview)
  - [Directory Structure](#directory-structure)
  - [Dockerfile Explanation](#dockerfile-explanation)
  - [Environment Variables](#environment-variables)
  - [Key Components](#key-components)
  - [Message Flow](#message-flow)
  - [Database Operations](#database-operations)
  - [Troubleshooting](#troubleshooting)

## Overview

The consumer service is a critical component of the Sensor Failure Detection System that:
- Subscribes to Kafka topics containing machine sensor readings
- Processes incoming messages and extracts sensor data
- Detects and tracks machine failures based on message contents
- Stores sensor readings and failure events in PostgreSQL
- Provides graceful shutdown handling

## Directory Structure

```
consumer/
├── Dockerfile                    # Multi-stage Docker build
├── pyproject.toml                # Project dependencies
├── consumer/
│   ├── __init__.py
│   ├── app.py                    # Main application entry point
│   ├── config.py                 # Configuration from environment variables
│   ├── services/
│   │   ├── __init__.py
│   │   ├── consumer.py           # Kafka consumer implementation
│   │   └── database.py           # Database operations
│   └── utils/
│       ├── __init__.py
│       └── shutdown.py           # Signal handling for graceful shutdown
└── README.md                     # This documentation file
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
COPY consumer/pyproject.toml consumer/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir uv && \
    cd domain && uv pip install --system -e . && \
    cd ../consumer && uv pip install --system -e .

COPY domain/ /app/domain/
COPY consumer/ /app/consumer/

FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/domain ./domain
COPY --from=builder /app/consumer ./consumer
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENV PYTHONPATH=/app

CMD ["python", "-m", "consumer.app"]
```

Key aspects:
- Uses Python 3.10 slim image for both build and runtime stages
- Installs build dependencies only in the first stage
- Utilises `uv` for fast and cached dependency installation
- Includes the domain module as a dependency
- Sets the proper `PYTHONPATH` for module imports
- Final image contains only runtime dependencies

## Environment Variables

| Environment Variable | Description | Default | Required |
| -------------------- | ----------- | ------- | -------- |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | localhost:9092 | Yes |
| `KAFKA_TOPIC` | Topic to consume messages from | machine.sensor.readings | Yes |
| `KAFKA_GROUP_ID` | Consumer group identifier | sensor-consumer-group | Yes |
| `POSTGRES_HOST` | PostgreSQL server hostname | localhost | Yes |
| `POSTGRES_PORT` | PostgreSQL server port | 5432 | Yes |
| `POSTGRES_USER` | PostgreSQL username | sensor_user | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | sensor_password | Yes |
| `POSTGRES_DB` | PostgreSQL database name | sensor_data | Yes |
| `BATCH_SIZE` | Number of messages to process in a batch | 100 | No |
| `COMMIT_INTERVAL_MS` | Interval for Kafka auto-commits (ms) | 5000 | No |

## Key Components

The consumer service consists of three main components:

1. **Kafka Consumer (`consumer.py`)**
   - Subscribes to the specified Kafka topic
   - Deserializes incoming messages from JSON format
   - Forwards messages to the database service
   - Handles Kafka-related errors and re-connections
   - Supports graceful shutdown

2. **Database Service (`database.py`)**
   - Processes incoming messages and extracts data
   - Creates or updates machine records
   - Detects and tracks failure events
   - Stores sensor readings with associated metadata
   - Uses Tortoise ORM for database operations

3. **Application Runner (`app.py`)**
   - Initialises the database connection
   - Creates and starts the Kafka consumer
   - Sets up signal handlers for graceful shutdown
   - Manages the application lifecycle

## Message Flow

1. Producer sends sensor data in JSON format to Kafka topic
2. Consumer subscribes to the topic and receives messages
3. Messages are deserialized and validated
4. For each message:
   - Machine record is created or updated
   - Failure state is tracked (start/end of failures)
   - Sensor readings are stored with timestamps
5. Processed offsets are committed to Kafka

## Database Operations

The service interacts with three main database models:

1. **Machine**: Represents physical machines sending sensor data
   - Tracks first and last seen timestamps
   - One-to-many relationship with readings and failures

2. **SensorReading**: Contains individual sensor measurements
   - Stores timestamp and sensor values as JSON
   - Links to the source machine
   - Optional link to an active failure if present

3. **Failure**: Represents a failure episode
   - Records start time, end time, and active status
   - Links to the affected machine
   - One-to-many relationship with sensor readings during the failure

## Troubleshooting

Common issues and their solutions:

1. **Consumer not receiving messages**
   - Verify Kafka broker connectivity
   - Check topic name and consumer group ID
   - Ensure the topic exists and has messages
   - Verify network connectivity between containers

2. **Database connection issues**
   - Check PostgreSQL connection parameters
   - Verify PostgreSQL container is running
   - Ensure database and user exist with proper permissions
   - Check for network connectivity between containers

3. **JSON parsing errors**
   - Verify message format from the producer
   - Check logs for specific parsing errors
   - Ensure timestamp format follows ISO 8601

4. **High memory usage**
   - Review the `BATCH_SIZE` setting
   - Implement batching for database operations
   - Consider scaling horizontally with multiple consumers
