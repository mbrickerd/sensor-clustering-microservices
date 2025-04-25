"""
Route definitions for the ML Training Service API.

This package contains the FastAPI route handlers for various API
endpoints, organised by functionality.
"""

from .health import router as health
from .train import router as train

__all__ = ["health", "train"]
