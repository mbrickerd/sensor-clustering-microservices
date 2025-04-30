"""
Health monitoring service for the Sensor Data Producer Service.

This module provides a service for monitoring and reporting the health
of the producer service, including metrics collection and exposure via
Prometheus.
"""

import time
from loguru import logger

from producer.utils.metrics import (
    MESSAGES_SENT,
    FAILURE_EVENTS,
    ACTIVE_FAILURES,
    MESSAGE_SEND_ERRORS,
)

from producer.utils import start_health_server


class HealthService:
    """
    Service for monitoring and reporting health metrics of the producer service.
    
    This class provides methods to track and update various operational metrics
    of the sensor data producer, such as message counts, failure events, and
    processing times. It integrates with Prometheus metrics for external monitoring.
    
    Attributes:
        `messages_sent`: Counter for tracking total number of messages sent
        `failure_events`: Counter for tracking total number of simulated failures
        `active_failures`: Gauge for tracking number of currently active failures
        `message_errors`: Counter for tracking message send errors
        `start_time`: Time when the service was initialized
    """
    
    def __init__(self) -> None:
        """
        Initialize the health service and start the metrics server.
        
        Sets up initial values for all metrics and starts the HTTP server
        for health checks and Prometheus metrics exposure.
        
        Returns:
            `None`
        """
        self.messages_sent = MESSAGES_SENT
        self.failure_events = FAILURE_EVENTS
        self.active_failures = ACTIVE_FAILURES
        self.message_errors = MESSAGE_SEND_ERRORS
        self.start_time = time.time()
        
        try:
            start_health_server()
            logger.info("Health metrics server started on port 8080 (/health) and 8000 (/metrics)")
            
        except Exception as err:
            logger.warning(f"Failed to start metrics server: {err}")
    
    def increment_messages_sent(self, count: int = 1) -> None:
        """
        Increment the count of messages sent to Event Hub.
        
        Args:
            `count`: Number of messages to add to the counter. Defaults to 1.
            
        Returns:
            `None`
        """
        self.messages_sent.inc(count)
    
    def increment_failure_events(self, count: int = 1) -> None:
        """
        Increment the count of simulated machine failures.
        
        Args:
            `count`: Number of failures to add to the counter. Defaults to 1.
            
        Returns:
            `None`
        """
        self.failure_events.inc(count)
    
    def set_active_failures(self, count: int) -> None:
        """
        Set the current number of active machine failures.
        
        Args:
            `count`: Current number of active failures
            
        Returns:
            `None`
        """
        self.active_failures.set(count)
    
    def increment_message_errors(self, count: int = 1) -> None:
        """
        Increment the count of message send errors.
        
        Args:
            `count`: Number of errors to add to the counter. Defaults to 1.
            
        Returns:
            `None`
        """
        self.message_errors.inc(count)
    
    def observe_processing_time(self, seconds: float) -> None:
        """
        Record message processing time.
        
        This method is a placeholder for future implementation of a histogram
        metric to track message processing times. Currently, it logs the time
        if it exceeds a threshold.
        
        Args:
            `seconds`: Processing time in seconds
            
        Returns:
            `None`
        """
        if seconds > 0.5:
            logger.warning(f"Slow message processing: {seconds:.3f}s")
    
    def get_uptime_seconds(self) -> float:
        """
        Get the service uptime in seconds.
        
        Returns:
            `float`: Number of seconds the service has been running
        """
        return time.time() - self.start_time
    
    def check_health(self) -> bool:
        """
        Perform a health check of the service.
        
        In a more complete implementation, this would check connectivity
        to Event Hubs and other dependencies. Currently just confirms
        the service is up.
        
        Returns:
            `bool`: `True` if the service is healthy, `False` otherwise
        """
        return True