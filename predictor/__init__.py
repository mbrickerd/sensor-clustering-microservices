"""
ML prediction service for the Sensor Failure Detection System.

This package provides the prediction service that loads trained clustering models
from MLflow and applies them to sensor readings stored in PostgreSQL. It performs
real-time inference, detects data drift, and exposes monitoring metrics.

The package is responsible for:
- Loading trained models from MLflow
- Processing new sensor readings from the database
- Predicting cluster assignments for sensor readings
- Detecting data drift and alerting when distribution changes
- Exposing Prometheus metrics for monitoring
- Automatically updating when new models are deployed
"""
