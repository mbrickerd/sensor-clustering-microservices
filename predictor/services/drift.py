"""
Drift detection service for the ML Prediction Service.

This module provides functionality to detect data drift in predictions
made by the machine learning models. It uses a sliding window approach
to monitor distribution changes over time and calculates divergence
metrics to quantify drift. It also exposes Prometheus metrics for
monitoring and alerting.
"""

from collections import deque
from typing import Deque

import numpy as np
from loguru import logger
from prometheus_client import Counter, Gauge, Histogram, start_http_server

from domain.models import DriftEvent
from predictor.config import config


class DriftDetectorService:
    """
    Service for detecting drift in model predictions.

    This class monitors the distribution of cluster predictions over time,
    detects significant changes (drift) from an established reference
    distribution, and exposes metrics for monitoring. It uses Jensen-Shannon
    divergence to quantify the difference between distributions and provides
    mechanisms to record drift events when they exceed a threshold.

    The service maintains a sliding window of recent cluster distributions
    and compares it to a reference distribution established after the initial
    window is filled. It handles the entire lifecycle of drift detection:
    metric collection, distribution comparison, and event recording.

    Attributes:
        window_size (`int`): Size of the sliding window for drift detection
        threshold (`float`): Threshold for drift detection (0-1)
        cluster_distribution (`Deque`): Sliding window of recent distributions
        reference_distribution (`dict`): Baseline distribution for comparison
        predictions_total (`Counter`): Prometheus counter for total predictions
        predictions_by_cluster (`Counter`): Prometheus counter for per-cluster predictions
        drift_score (`Gauge`): Prometheus gauge for current drift score
        drift_detected (`Gauge`): Prometheus gauge for drift detection status
        prediction_latency (`Histogram`): Prometheus histogram for prediction timing
        metrics_port (`int`): Port where Prometheus metrics are exposed
    """

    def __init__(self, window_size: int | None = None) -> None:
        """
        Initialise the drift detector.

        Sets up the sliding window for tracking distributions, initialises
        Prometheus metrics, and starts the metrics HTTP server. Uses the
        configured window size and threshold from application configuration
        or allows them to be overridden.

        Args:
            window_size (`int`, optional): Size of the sliding window for drift detection.
                If `None`, uses the value from configuration.
        """
        self.window_size = window_size or config.drift_detection_window
        self.threshold = config.drift_threshold
        self.cluster_distribution: Deque[dict[int, float]] = deque(
            maxlen=self.window_size
        )
        self.reference_distribution: dict[int, float] | None = None

        # Initialise Prometheus metrics
        self.predictions_total = Counter(
            "sensor_predictions_total", "Total number of predictions made"
        )
        self.predictions_by_cluster = Counter(
            "sensor_predictions_by_cluster", "Predictions by cluster ID", ["cluster_id"]
        )
        self.drift_score = Gauge(
            "sensor_drift_score", "Current drift score for prediction distribution"
        )
        self.drift_detected = Gauge(
            "sensor_drift_detected", "Whether drift has been detected (1) or not (0)"
        )
        self.prediction_latency = Histogram(
            "sensor_prediction_latency_seconds",
            "Time taken for prediction",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        )
        self.metrics_port = config.metrics_port

        try:
            start_http_server(self.metrics_port)
            logger.info(
                f"Started Prometheus metrics server on port {self.metrics_port}"
            )

        except Exception as err:
            logger.error(f"Failed to start Prometheus metrics server: {err}")

    def update_metrics(self, clusters: list[int], latency: float) -> float:
        """
        Update metrics with new predictions.

        This function updates all Prometheus metrics with new prediction data,
        adds the current cluster distribution to the sliding window, and
        calculates the current drift score. If the drift score exceeds the
        threshold, it logs a warning.

        Args:
            clusters (`list[int]`): List of predicted cluster IDs from recent predictions
            latency (`float`): Time taken for predictions in seconds

        Returns:
            `float`: Current drift score (0-1), or 0.0 if reference distribution
                is not yet established
        """
        if not clusters:
            return 0.0

        self.predictions_total.inc(len(clusters))
        self.prediction_latency.observe(latency)

        for cluster in clusters:
            self.predictions_by_cluster.labels(cluster_id=str(cluster)).inc()

        distribution = self._calculate_distribution(clusters)
        self.cluster_distribution.append(distribution)

        if (
            self.reference_distribution is None
            and len(self.cluster_distribution) >= self.window_size
        ):
            self._set_reference_distribution()

        drift_score = 0.0
        if self.reference_distribution is not None:
            drift_score = self._calculate_drift()
            self.drift_score.set(drift_score)
            self.drift_detected.set(1 if drift_score > self.threshold else 0)

            if drift_score > self.threshold:
                logger.warning(f"Drift detected! Score: {drift_score:.4f}")

        return drift_score

    def _calculate_distribution(self, clusters: list[int]) -> dict[int, float]:
        """
        Calculate the distribution of clusters.

        Converts a list of cluster assignments into a normalised frequency
        distribution, where each key is a cluster ID and each value is the
        relative frequency of that cluster (0-1).

        Args:
            clusters (`list[int]`): List of cluster assignments

        Returns:
            `dict[int, float]`: Normalized frequency distribution of clusters
        """
        distribution: dict[int, float] = {}
        total = len(clusters)
        for cluster in clusters:
            distribution[cluster] = distribution.get(cluster, 0) + 1
        return {k: v / total for k, v in distribution.items()}

    def _set_reference_distribution(self) -> None:
        """
        Set the reference distribution for drift detection.

        This method is called once the sliding window is filled to establish
        the baseline distribution against which future distributions will be
        compared. It aggregates all distributions in the current window to
        create a stable reference.

        Returns:
            `None`
        """
        reference: dict[int, float] = {}
        for dist in self.cluster_distribution:
            for cluster, count in dist.items():
                reference[cluster] = reference.get(cluster, 0) + count

        total = sum(reference.values())
        self.reference_distribution = {k: v / total for k, v in reference.items()}

    def _calculate_drift(self) -> float:
        """
        Calculate drift between current and reference distributions.

        This method computes the average distribution across the current sliding
        window and measures its divergence from the reference distribution using
        Jensen-Shannon divergence. It ensures that all clusters present in either
        distribution are accounted for by adding zero-valued entries as needed.

        Returns:
            `float`: JS divergence as a drift score between 0 and 1, where higher
                values indicate more significant drift
        """
        if not self.reference_distribution or len(self.cluster_distribution) == 0:
            return 0.0

        current: dict[int, float] = {}
        for dist in self.cluster_distribution:
            for cluster, freq in dist.items():
                if cluster in current:
                    current[cluster] += freq
                else:
                    current[cluster] = freq

        total = sum(current.values())
        if total > 0:
            for cluster in current:
                current[cluster] /= total

        all_clusters = set(self.reference_distribution.keys()) | set(current.keys())

        for cluster in all_clusters:
            if cluster not in self.reference_distribution:
                self.reference_distribution[cluster] = 0.0
            if cluster not in current:
                current[cluster] = 0.0

        return self._js_divergence(current, self.reference_distribution)

    def _kl_divergence(self, p: dict[int, float], q: dict[int, float]) -> float:
        """
        Calculate Kullback-Leibler divergence between two distributions.

        KL divergence is a measure of how one probability distribution diverges
        from a second, expected probability distribution. This implementation
        only considers pairs of values where both are positive to avoid division
        by zero or log of zero.

        Args:
            p (`dict[int, float]`): First distribution as {cluster_id: frequency}
            q (`dict[int, float]`): Second distribution as {cluster_id: frequency}

        Returns:
            `float`: KL divergence value (unbounded, non-symmetric)
        """
        divergence = 0.0

        for k in p:
            if p[k] > 0 and q[k] > 0:
                divergence += p[k] * np.log(p[k] / q[k])

        return divergence

    def _js_divergence(self, p: dict[int, float], q: dict[int, float]) -> float:
        """
        Calculate Jensen-Shannon divergence between two distributions.

        JS divergence is a symmetric and smoothed version of KL divergence.
        It is calculated as the average of the KL divergence of each distribution
        to the average of both distributions. The resulting value is normalized
        to the range [0, 1].

        Args:
            p (`dict[int, float]`): First distribution as {cluster_id: frequency}
            q (`dict[int, float]`): Second distribution as {cluster_id: frequency}

        Returns:
            `float`: JS divergence (between 0 and 1), where 0 indicates identical
                distributions and 1 indicates maximum divergence
        """
        m: dict[int, float] = {}
        for k in set(p.keys()) | set(q.keys()):
            m[k] = (p.get(k, 0) + q.get(k, 0)) / 2

        js_div = (self._kl_divergence(p, m) + self._kl_divergence(q, m)) / 2

        return min(1.0, max(0.0, js_div))

    async def record_drift_event(
        self, drift_score: float, current_distribution: dict[int, float]
    ) -> None:
        """
        Record a drift event in the database.

        When drift exceeds the threshold, this method creates a record in the
        database with the current drift score, reference distribution, and
        current distribution for later analysis.

        Args:
            drift_score (`float`): The calculated drift score
            current_distribution (`dict[int, float]`): The current cluster distribution

        Returns:
            `None`
        """
        await DriftEvent.create(
            drift_score=drift_score,
            reference_distribution=self.reference_distribution,
            current_distribution=current_distribution,
        )
        logger.info(f"Recorded drift event with score {drift_score}")
