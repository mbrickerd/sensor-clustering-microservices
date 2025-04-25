"""
Service modules for the ML Prediction Service.

This package contains service classes that provide the core functionality
of the predictor service, including model loading, prediction, and
drift detection capabilities.
"""

from .drift import DriftDetectorService
from .predictor import PredictorService

__all__ = ["DriftDetectorService", "PredictorService"]
