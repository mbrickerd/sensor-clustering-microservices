from producer.services.server import ServerService


def start_health_server(health_port: int = 8080, metrics_port: int = 8000) -> bool:
    """
    Start the HTTP servers for health checks and Prometheus metrics.
    
    This is a convenience function that gets or creates the ServerService
    singleton and starts it.
    
    Args:
        `health_port`: Port number for the health check HTTP server
        `metrics_port`: Port number for the Prometheus metrics server
        
    Returns:
        `bool`: `True` if servers were started by this call, `False` if already running
    """
    server_service = ServerService.get_instance(health_port, metrics_port)
    return server_service.start()