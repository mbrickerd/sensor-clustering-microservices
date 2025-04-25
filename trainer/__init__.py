"""
ML training service for the Sensor Failure Detection System.

This package provides the training service that analyzes sensor data,
builds clustering models for failure patterns, and registers them with
MLflow. It supports both direct execution and API-driven operation,
with jobs processed through Celery for distributed execution.

The package is responsible for:
- Loading historical failure data from the database
- Extracting features from sensor readings
- Clustering failures based on sensor patterns
- Comparing clusters to known failure types
- Registering models in MLflow for inference
- Notifying other services about new models
"""
