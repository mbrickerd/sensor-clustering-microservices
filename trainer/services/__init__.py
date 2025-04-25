"""
Service modules for the ML Training Service.

This package contains service classes that provide the core functionality
of the training service, including data loading, model training, and
interaction with MLflow.
"""

from .trainer import TrainerService

__all__ = ["TrainerService"]
