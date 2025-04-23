from prometheus_client import Counter, Gauge, Histogram, start_http_server
import numpy as np
from loguru import logger
from collections import deque
from domain.models import DriftEvent


from predictor.config import config


class DriftDetectorService:
    """Service for detecting drift in model predictions."""
    
    def __init__(self, window_size: int = None):
        """Initialize the drift detector.
        
        Args:
            window_size: Size of the sliding window for drift detection
        """
        self.window_size = window_size or config.drift_detection_window
        self.threshold = config.drift_threshold
        
        # Sliding windows for metrics
        self.cluster_distribution = deque(maxlen=self.window_size)
        self.reference_distribution = None
        
        # Initialize Prometheus metrics
        self.predictions_total = Counter(
            'sensor_predictions_total', 'Total number of predictions made'
        )
        self.predictions_by_cluster = Counter(
            'sensor_predictions_by_cluster', 'Predictions by cluster ID',
            ['cluster_id']
        )
        self.drift_score = Gauge(
            'sensor_drift_score', 'Current drift score for prediction distribution'
        )
        self.drift_detected = Gauge(
            'sensor_drift_detected', 'Whether drift has been detected (1) or not (0)'
        )
        self.prediction_latency = Histogram(
            'sensor_prediction_latency_seconds', 'Time taken for prediction',
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
        
        # Start Prometheus HTTP server
        self.metrics_port = config.metrics_port
        try:
            start_http_server(self.metrics_port)
            logger.info(f"Started Prometheus metrics server on port {self.metrics_port}")
            
        except Exception as err:
            logger.error(f"Failed to start Prometheus metrics server: {err}")
    
    def update_metrics(self, clusters: list[int], latency: float) -> float:
        """Update metrics with new predictions.
        
        Args:
            clusters: List of predicted cluster IDs
            latency: Time taken for predictions in seconds
        """
        if not clusters:
            return
            
        # Update general metrics
        self.predictions_total.inc(len(clusters))
        self.prediction_latency.observe(latency)
        
        # Update cluster-specific metrics
        for cluster in clusters:
            self.predictions_by_cluster.labels(cluster_id=str(cluster)).inc()
        
        # Add current distribution to sliding window
        distribution = self._calculate_distribution(clusters)
        self.cluster_distribution.append(distribution)
        
        # If we don't have a reference distribution yet, set it
        if self.reference_distribution is None and len(self.cluster_distribution) >= self.window_size:
            self._set_reference_distribution()
        
        # Calculate drift if we have a reference distribution
        drift_score = 0.0
        if self.reference_distribution is not None:
            drift_score = self._calculate_drift()
            self.drift_score.set(drift_score)
            self.drift_detected.set(1 if drift_score > self.threshold else 0)
            
            if drift_score > self.threshold:
                logger.warning(f"Drift detected! Score: {drift_score:.4f}")
                
        return drift_score
    
    def _calculate_distribution(self, clusters: list[int]) -> dict[int, float]:
        """Calculate the distribution of clusters in a batch.
        
        Args:
            clusters: List of cluster IDs
            
        Returns:
            Dictionary mapping cluster IDs to their frequency
        """
        distribution = {}
        total = len(clusters)
        
        if total == 0:
            return distribution
            
        for cluster in clusters:
            if cluster in distribution:
                distribution[cluster] += 1
                
            else:
                distribution[cluster] = 1
                
        # Normalize to frequencies
        for cluster in distribution:
            distribution[cluster] /= total
            
        return distribution
    
    def _set_reference_distribution(self) -> None:
        """Set the reference distribution for drift detection."""
        if len(self.cluster_distribution) < self.window_size:
            return
            
        # Average the distributions in the window
        reference = {}
        
        for dist in self.cluster_distribution:
            for cluster, freq in dist.items():
                if cluster in reference:
                    reference[cluster] += freq
                else:
                    reference[cluster] = freq
        
        # Normalize
        total = sum(reference.values())
        if total > 0:
            for cluster in reference:
                reference[cluster] /= total
        
        self.reference_distribution = reference
        logger.info(f"Set reference distribution: {self.reference_distribution}")
    
    def _calculate_drift(self) -> float:
        """Calculate drift between current and reference distributions.
        
        Returns:
            JS divergence as a drift score between 0 and 1
        """
        if not self.reference_distribution or len(self.cluster_distribution) == 0:
            return 0.0
            
        # Get current distribution (average of sliding window)
        current = {}
        for dist in self.cluster_distribution:
            for cluster, freq in dist.items():
                if cluster in current:
                    current[cluster] += freq
                else:
                    current[cluster] = freq
        
        # Normalize
        total = sum(current.values())
        if total > 0:
            for cluster in current:
                current[cluster] /= total
        
        # Ensure all clusters in reference are in current and vice versa
        all_clusters = set(self.reference_distribution.keys()) | set(current.keys())
        
        for cluster in all_clusters:
            if cluster not in self.reference_distribution:
                self.reference_distribution[cluster] = 0.0
            if cluster not in current:
                current[cluster] = 0.0
        
        # Calculate Jensen-Shannon divergence
        return self._js_divergence(current, self.reference_distribution)
    
    def _kl_divergence(self, p: dict[int, float], q: dict[int, float]) -> float:
        """Calculate Kullback-Leibler divergence between two distributions.
        
        Args:
            p: First distribution
            q: Second distribution
            
        Returns:
            KL divergence
        """
        divergence = 0.0
        
        for k in p:
            if p[k] > 0 and q[k] > 0:
                divergence += p[k] * np.log(p[k] / q[k])
                
        return divergence
    
    def _js_divergence(self, p: dict[int, float], q: dict[int, float]) -> float:
        """Calculate Jensen-Shannon divergence between two distributions.
        
        Args:
            p: First distribution
            q: Second distribution
            
        Returns:
            JS divergence (between 0 and 1)
        """
        # Create the average distribution
        m = {}
        for k in set(p.keys()) | set(q.keys()):
            m[k] = (p.get(k, 0) + q.get(k, 0)) / 2
        
        # Calculate JS divergence
        js_div = (self._kl_divergence(p, m) + self._kl_divergence(q, m)) / 2
        
        # Normalize to [0, 1]
        return min(1.0, max(0.0, js_div))
    
    async def record_drift_event(self, drift_score: float, current_distribution: dict[int, float]) -> None:
        """Record a drift event in the database.
        
        Args:
            drift_score: The calculated drift score
        """        
        await DriftEvent.create(
            drift_score=drift_score,
            reference_distribution=self.reference_distribution,
            current_distribution=current_distribution
        )
        logger.info(f"Recorded drift event with score {drift_score}")