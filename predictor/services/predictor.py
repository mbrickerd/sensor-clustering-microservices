"""
Prediction service for the ML Prediction Service.

This module provides the core prediction functionality for the Sensor Failure
Detection System. It loads trained clustering models from MLflow, processes
unprocessed sensor readings from the database, makes predictions, and
monitors for data drift. It also handles model updates when new versions
become available.
"""

import asyncio
import pickle
from time import time
from typing import Any

import numpy as np
from loguru import logger

import mlflow
import mlflow.sklearn
from domain.models import Cluster, ModelVersion, SensorPrediction, SensorReading
from mlflow.tracking import MlflowClient
from predictor.config import config
from predictor.services.drift import DriftDetectorService


class PredictorService:
    """
    Service for making predictions on sensor data using trained models.

    This class is responsible for the core prediction workflow of the system.
    It loads clustering models from MLflow, processes batches of sensor readings
    from the database, extracts features, makes predictions, stores results,
    and integrates with the drift detection service for monitoring.

    The service runs in a continuous loop, periodically checking for new
    readings to process and new models to load. It implements robust error
    handling and automatic model updating when new versions are available.

    Attributes:
        `model`: The loaded scikit-learn clustering model
        `scaler`: The feature scaler associated with the model
        `feature_cols`: List of feature column names expected by the model
        `cluster_profiles`: Profiles describing each cluster's characteristics
        `drift_detector`: Service for monitoring data drift
    """

    def __init__(self) -> None:
        """
        Initialise the prediction service.

        Sets up the prediction service with empty model attributes that will
        be populated when a model is loaded. Creates a drift detector instance
        and configures the MLflow connection for model loading.

        Returns:
            `None`
        """
        self.model = None
        self.scaler = None
        self.feature_cols = None
        self.cluster_profiles = None

        self.drift_detector = DriftDetectorService()

        mlflow.set_tracking_uri(config.mlflow_tracking_uri)  # type: ignore

    async def load_active_model(self) -> bool:
        """
        Load the active model from MLflow, using the database to determine which one.

        Queries the database for the currently active clustering model, then loads
        the model and its associated artifacts (scaler, feature definitions, cluster
        profiles) from MLflow. This method handles the complete model loading
        process including error handling.

        Returns:
            `bool`: `True` if a model was successfully loaded, `False` otherwise
        """
        try:
            active_model = await Cluster.filter(is_active=True).order_by("-id").first()

            if not active_model:
                logger.warning("No active model found in database")
                return False

            logger.info(
                f"Loading model from MLflow (Run ID: {active_model.mlflow_run_id}, "
                f"Version: {active_model.mlflow_model_version})"
            )

            try:
                self.model = mlflow.sklearn.load_model(
                    f"runs:/{active_model.mlflow_run_id}/kmeans_model"
                )

                client = mlflow.tracking.MlflowClient()
                scaler_path = client.download_artifacts(
                    active_model.mlflow_run_id, "scaler.pkl"
                )
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)

                self.cluster_profiles = active_model.cluster_profiles

                if self.cluster_profiles:
                    first_cluster = list(self.cluster_profiles.values())[0]
                    all_features = first_cluster.get("all_features", {})
                    self.feature_cols = list(all_features.keys())

                logger.info(
                    f"Successfully loaded model (n_clusters: {active_model.n_clusters})"
                )
                return True

            except Exception as err:
                logger.error(f"Error loading model from MLflow: {err}")
                return False

        except Exception as err:
            logger.error(f"Error getting active model: {err}")
            return False

    async def get_unprocessed_readings(
        self, batch_size: int | None = None
    ) -> list[SensorReading]:
        """
        Get sensor readings that haven't been processed yet.

        Queries the database for sensor readings that don't have predictions
        and aren't associated with failures. Limits the number of readings
        returned based on the batch size configuration to avoid overwhelming
        the system.

        Args:
            batch_size (`int`, optional): Maximum number of readings to retrieve.
                If `None`, uses the value from configuration.

        Returns:
            `list[SensorReading]`: List of unprocessed sensor readings
        """
        if batch_size is None:
            batch_size = config.prediction_batch_size

        readings = (
            await SensorReading.filter(predictions=None, failure=None)
            .order_by("timestamp")
            .limit(batch_size)
            .prefetch_related("machine")
        )

        return readings

    def extract_features(self, reading: SensorReading) -> dict[str, float] | None:
        """
        Extract features from a single sensor reading.

        Converts a raw sensor reading into the feature format expected by the
        model. This includes handling different feature types (mean, std, min, max)
        and ensuring all expected features are present with appropriate default
        values for missing sensors.

        Args:
            reading (SensorReading): The sensor reading to extract features from

        Returns:
            `dict[str, float] | None`: Dictionary of feature name to value mappings,
                or `None` if feature extraction fails
        """
        if not self.feature_cols:
            logger.error("Feature columns not loaded")
            return None

        values = reading.values_dict
        if not values:
            logger.warning(f"No values found for reading {reading.id}")
            return None

        features = {}
        for feature in self.feature_cols:
            if feature is None:
                continue

            if "_mean" in feature:
                sensor_name = feature.split("_mean")[0]
                if sensor_name in values:
                    features[f"{sensor_name}_mean"] = values[sensor_name]
                    features[f"{sensor_name}_std"] = 0.0
                    features[f"{sensor_name}_min"] = values[sensor_name]
                    features[f"{sensor_name}_max"] = values[sensor_name]

                else:
                    features[f"{sensor_name}_mean"] = 0.0
                    features[f"{sensor_name}_std"] = 0.0
                    features[f"{sensor_name}_min"] = 0.0
                    features[f"{sensor_name}_max"] = 0.0

            elif "_std" in feature or "_min" in feature or "_max" in feature:
                continue

            else:
                feature_parts = feature.split("_")
                if len(feature_parts) > 1:
                    sensor_name = "_".join(feature_parts[:-1])
                    if sensor_name in values:
                        features[feature] = values[sensor_name]

                    else:
                        features[feature] = 0.0
                else:
                    if feature in values:
                        features[feature] = values[feature]

                    else:
                        features[feature] = 0.0

        return features

    def predict_cluster(self, features: dict[str, float]) -> int | None:
        """
        Predict cluster for a set of features.

        Applies the loaded clustering model to a set of extracted features to
        determine the cluster assignment. Handles feature vector construction,
        scaling, and prediction.

        Args:
            features (`dict[str, float]`): Feature dictionary extracted from a sensor reading

        Returns:
            `int | None`: Predicted cluster ID, or `None` if prediction fails
        """
        if not self.model or not self.scaler or not self.feature_cols:
            logger.error("Model, scaler, or feature columns not loaded")
            return None

        feature_vector = []
        for col in self.feature_cols:
            feature_vector.append(features.get(col, 0.0))

        feature_vector = np.array(feature_vector).reshape(1, -1)
        feature_vector_scaled = self.scaler.transform(feature_vector)

        cluster = self.model.predict(feature_vector_scaled)[0]
        return int(cluster)

    async def process_readings(self) -> tuple[int, list[int]]:
        """
        Process unprocessed readings and make predictions.

        This method forms the core of the prediction workflow. It retrieves
        unprocessed readings, extracts features, makes predictions, and stores
        the results in the database. It also updates drift metrics and records
        drift events when necessary.

        Returns:
            `tuple[int, list[int]]`: Number of processed readings and list of predicted clusters
        """
        start_time = time()

        if not self.model or not self.scaler or not self.feature_cols:
            return 0, []

        readings = await self.get_unprocessed_readings(config.prediction_batch_size)

        if not readings:
            return 0, []

        processed_count = 0
        predicted_clusters = []
        active_model = await Cluster.filter(is_active=True).first()
        if not active_model:
            logger.error("No active model found despite previously loading one")
            return 0, []

        model_version = active_model.mlflow_model_version
        mlflow_run_id = active_model.mlflow_run_id

        for reading in readings:
            features = self.extract_features(reading)
            if not features:
                continue

            cluster = self.predict_cluster(features)
            if cluster is None:
                continue

            try:
                await SensorPrediction.create(
                    reading=reading,
                    cluster_id=cluster,
                    model_version=model_version,
                    confidence_score=None,
                    mlflow_run_id=mlflow_run_id,
                )

                logger.debug(
                    f"Created prediction for reading {reading.id}, cluster {cluster}"
                )

                predicted_clusters.append(cluster)
                processed_count += 1

            except Exception as err:
                logger.error(f"Error creating prediction: {err}")

        processing_time = time() - start_time
        drift_score = self.drift_detector.update_metrics(
            predicted_clusters, processing_time
        )

        if drift_score > self.drift_detector.threshold:
            current_dist = self.drift_detector._calculate_distribution(
                predicted_clusters
            )
            await self.drift_detector.record_drift_event(drift_score, current_dist)

        logger.info(
            f"Processed {processed_count} readings in {processing_time:.4f} seconds"
        )
        return processed_count, predicted_clusters

    async def check_new_model(self) -> bool:
        """
        Check if there are new models to be processed.

        Queries the database for notifications about new model versions that
        have been registered but not yet processed by the prediction service.
        Marks any found notifications as processed to avoid duplicate processing.

        Returns:
            `bool`: `True` if a new model version was found, `False` otherwise
        """
        try:
            new_version = (
                await ModelVersion.filter(is_processed=False)
                .order_by("-created_at")
                .first()
            )

            if new_version:
                logger.info(
                    f"Found new model version: {new_version.version}, "
                    f"run ID: {new_version.run_id}"
                )
                new_version.is_processed = True
                await new_version.save()

                return True

            return False

        except Exception as err:
            logger.error(f"Error checking for new models: {err}")
            return False

    async def run(self) -> None:
        """
        Run the inference loop, waiting for model before processing readings.

        This is the main entry point for the prediction service. It first waits
        for a valid model to be available, then enters a continuous loop of checking
        for new models, processing readings, and waiting for the next cycle.
        The method implements robust error handling and recovery mechanisms.

        Returns:
            `None`
        """
        logger.info("Starting inference service - waiting for a model...")

        while not await self.load_active_model():
            new_model = await self.check_new_model()
            if new_model:
                logger.info(
                    "New model notification received, attempting to load model..."
                )
                if await self.load_active_model():
                    logger.info("Model loaded successfully, starting processing...")
                    break

            if not hasattr(self, "_waiting_for_model_logged"):
                logger.info("Waiting for an active model to be available...")
                self._waiting_for_model_logged = True

            await asyncio.sleep(config.inference_interval_seconds)

        logger.info("Starting main processing loop with loaded model")
        while True:
            try:
                new_model = await self.check_new_model()
                if new_model:
                    logger.info("Loading new model version...")
                    await self.load_active_model()

                processed, clusters = await self.process_readings()
                if processed > 0:
                    logger.info(
                        f"Processed {processed} readings with {len(set(clusters))} different clusters"
                    )

                await asyncio.sleep(config.inference_interval_seconds)

            except Exception as err:
                logger.error(f"Error in inference loop: {err}")
                await asyncio.sleep(config.inference_interval_seconds)

    def get_cluster_description(self, cluster_id: int) -> dict[str, Any]:
        """
        Get the description of a cluster from the profiles.

        Retrieves the characteristics and metadata for a specific cluster
        from the loaded cluster profiles. This information can be used to
        provide human-readable interpretations of what each cluster represents.

        Args:
            cluster_id (`int`): The cluster ID to get the description for

        Returns:
            `dict[str, Any]`: Dictionary containing cluster profile information,
                or an error message if the cluster is not found
        """
        if not self.cluster_profiles:
            return {"error": "No cluster profiles loaded"}

        cluster_key = f"cluster_{cluster_id}"
        if cluster_key not in self.cluster_profiles:
            return {"error": f"Cluster {cluster_id} not found in profiles"}

        return self.cluster_profiles[cluster_key]
