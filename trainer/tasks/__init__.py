"""
Celery tasks for the ML Training Service.

This package contains Celery task definitions for asynchronous
execution of training jobs in a distributed environment.
"""

from .train import train_model

__all__ = ["train_model"]
