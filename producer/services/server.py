"""
HTTP server service for health checks and metrics.

This service provides an HTTP server that exposes endpoints for health checks
and readiness probes, typically used by container orchestration systems like
Kubernetes to determine if the service is healthy and ready to accept traffic.
"""

import threading
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Type, ClassVar, Union
from prometheus_client import start_http_server
from loguru import logger


class HealthHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for health check endpoints.
    
    This handler processes incoming HTTP requests and responds to different
    health-related endpoints:
    - /health: Basic health check indicating the service is running
    - /ready: Readiness check indicating the service is ready to accept traffic
    - /status: Detailed status information about the service (JSON)
    
    Attributes:
        `server_service`: Reference to the server service that created this handler
    """
    
    server_service: ClassVar[Union['ServerService', None]] = None
    
    def do_GET(self) -> None:
        """
        Handle GET requests to the health endpoints.
        
        Returns standard HTTP responses based on the requested path:
        - 200 OK for valid health endpoints
        - 404 Not Found for unknown paths
        """
        if self.path == '/health':
            self._handle_health()
            
        elif self.path == '/ready':
            self._handle_ready()
            
        elif self.path == '/status':
            self._handle_status()
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def _handle_health(self) -> None:
        """Handle the /health endpoint with a simple 'OK' response."""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    
    def _handle_ready(self) -> None:
        """Handle the /ready endpoint with a simple 'READY' response."""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'READY')
    
    def _handle_status(self) -> None:
        """
        Handle the /status endpoint with JSON status information.
        
        Returns detailed status information about the service as JSON.
        """
        if self.server_service:
            status = {
                "status": "running",
                "uptime": time.time() - self.server_service.start_time,
                "version": "1.0.0"
            }
            
        else:
            status = {
                "status": "running",
                "error": "server_service not set",
                "version": "1.0.0"
            }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status).encode('utf-8'))
    
    def log_message(self, format: str, *args: Any) -> None:
        """Override to use loguru instead of stderr."""
        if not self.path == '/health':  # Don't log frequent health checks
            logger.debug(f"Health server: {format % args}")


class ServerService:
    """
    Service that provides HTTP endpoints for health monitoring.
    
    This service manages an HTTP server that exposes various health and status
    endpoints, and also initializes the Prometheus metrics server.
    
    Attributes:
        `health_port`: Port number for the health check server
        `metrics_port`: Port number for the Prometheus metrics server
        `server`: Instance of the HTTP server
        `server_thread`: Thread running the HTTP server
        `is_running`: Flag indicating if the server is running
        `start_time`: Time when the server was started
    """
    
    # Global singleton instance
    _instance: Union['ServerService', None] = None
    _instance_lock = threading.Lock()
    
    @classmethod
    def get_instance(cls, health_port: int = 8080, metrics_port: int = 8000) -> 'ServerService':
        """
        Get or create the singleton instance of the ServerService.
        
        This method ensures only one server is created and running, even if
        called multiple times from different parts of the application.
        
        Args:
            `health_port`: Port for the health HTTP server
            `metrics_port`: Port for the Prometheus metrics server
            
        Returns:
            `ServerService`: The singleton instance
        """
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = ServerService(health_port, metrics_port)
            return cls._instance
    
    def __init__(self, health_port: int = 8080, metrics_port: int = 8000):
        """
        Initialize the server service.
        
        Note: This constructor should not be called directly. Use the
        get_instance() class method instead to ensure proper singleton behavior.
        
        Args:
            `health_port`: Port number for the health check server
            `metrics_port`: Port number for the Prometheus metrics server
        """
        self.health_port = health_port
        self.metrics_port = metrics_port
        self.server: Union[HTTPServer, None] = None
        self.server_thread: Union[threading.Thread, None] = None
        self.is_running = False
        self.start_time: float = 0.0
    
    def create_handler_class(self) -> Type[BaseHTTPRequestHandler]:
        """
        Create a subclass of HealthHandler that has a reference to this service.
        
        Returns:
            `Type[BaseHTTPRequestHandler]`: A subclass of HealthHandler with 
                service reference set
        """
        class ConfiguredHandler(HealthHandler):
            server_service = self
        
        return ConfiguredHandler
    
    def start(self) -> bool:
        """
        Start the HTTP servers for health checks and Prometheus metrics.
        
        Returns:
            `bool`: True if servers were started by this call, False if already running
        """
        if self.is_running:
            logger.debug("Server service already running")
            return False
        
        try:
            # Start Prometheus metrics server
            start_http_server(self.metrics_port)
            logger.info(f"Prometheus metrics server started on port {self.metrics_port}")
            
            # Start health check server
            handler_class = self.create_handler_class()
            self.server = HTTPServer(('0.0.0.0', self.health_port), handler_class)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            logger.info(f"Health check server started on port {self.health_port}")
            
            self.is_running = True
            self.start_time = time.time()
            return True
            
        except Exception as err:
            logger.error(f"Failed to start metrics or health servers: {err}")
            return False
    
    def stop(self) -> None:
        """
        Stop the HTTP server if it's running.
        
        Returns:
            `None`
        """
        if self.server and self.is_running:
            self.server.shutdown()
            if self.server_thread:
                self.server_thread.join(timeout=5)
            self.is_running = False
            logger.info("Health HTTP server stopped")
    
    def get_uptime(self) -> float:
        """
        Get the server uptime in seconds.
        
        Returns:
            `float`: Number of seconds the server has been running
        """
        if not self.is_running:
            return 0.0
        
        return time.time() - self.start_time