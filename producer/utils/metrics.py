"""
Prometheus metrics definitions for the Sensor Data Producer Service.

This module centralizes all Prometheus metrics definitions used throughout
the application, ensuring consistency and avoiding duplication of metric names.
"""

from prometheus_client import Counter, Gauge, Histogram


MESSAGES_SENT = Counter(
    'sensor_producer_messages_sent_total', 
    'Total number of messages sent to Event Hub'
)

MESSAGE_SEND_ERRORS = Counter(
    'sensor_producer_message_errors_total', 
    'Total number of message send errors'
)

FAILURE_EVENTS = Counter(
    'sensor_producer_failure_events_total', 
    'Total number of simulated machine failures'
)

ACTIVE_FAILURES = Gauge(
    'sensor_producer_active_failures', 
    'Number of currently active failures'
)

PROCESSING_TIME = Histogram(
    'sensor_producer_processing_seconds', 
    'Time taken to process and send messages',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

MEMORY_USAGE = Gauge(
    'sensor_producer_memory_bytes',
    'Memory usage of the producer service in bytes'
)

CPU_USAGE = Gauge(
    'sensor_producer_cpu_usage_percent',
    'CPU usage of the producer service as a percentage'
)

EVENT_HUB_CONNECTIVITY = Gauge(
    'sensor_producer_eventhub_connected',
    'Whether the producer is connected to Event Hub (1=connected, 0=disconnected)'
)

STORAGE_CONNECTIVITY = Gauge(
    'sensor_producer_storage_connected',
    'Whether the producer is connected to Azure Storage (1=connected, 0=disconnected)'
)