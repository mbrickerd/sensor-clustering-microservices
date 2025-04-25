"""
Sensor Data Consumer Service.

This package provides a Kafka consumer service that processes sensor
data from machines, detects failures, and stores the data in PostgreSQL.
The service is designed to work as part of a larger system for monitoring
and analyzing sensor data from industrial machines.

Main components:
- Kafka consumer for message processing
- Database service for data storage
- Configuration management
- Signal handling for graceful shutdown
"""
