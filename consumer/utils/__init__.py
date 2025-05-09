"""
Utility modules for the Sensor Data Consumer Service.

This package contains utility functions and helper classes used
throughout the consumer service, including shutdown handling and
other common functionalities.
"""

from .shutdown import create_signal_handler, setup_signal_handlers, shutdown

__all__ = ["shutdown", "setup_signal_handlers", "create_signal_handler"]
