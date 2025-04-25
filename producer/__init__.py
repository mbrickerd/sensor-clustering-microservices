"""
Sensor data producer service for the Sensor Failure Detection System.

This package provides a simulation service that generates realistic machine
sensor readings and publishes them to Kafka for consumption by other components.
It simulates both normal machine operation and failure conditions based on
statistical models derived from reference data.

The package is responsible for:
- Generating realistic sensor readings that mimic actual machine behavior
- Simulating random failures based on learned or configured patterns
- Publishing messages to Kafka in a consistent, well-defined format
- Providing a configurable data source for testing and development
"""
