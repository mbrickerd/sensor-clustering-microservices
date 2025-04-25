"""
Core training service for the ML Training Service.

This module provides the main implementation of the training workflow
that loads historical failure data, extracts features, trains clustering
models, and registers them with MLflow for use by the prediction service.
"""

import json
import os
import pickle
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import numpy as np
import polars as pl
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from tortoise import Tortoise

import mlflow
import mlflow.sklearn
from domain.models import Cluster, Failure, ModelVersion, SensorReading, init_db
from mlflow.tracking import MlflowClient
from trainer.config import config


class TrainerService:
    """
    Service for analysing and clustering machine failures.

    This class is responsible for the core machine learning workflow of
    the system. It loads historical failure episodes from the database,
    extracts features from sensor readings, clusters similar failures,
    and analyses the characteristics of each cluster. It also handles
    MLflow integration for model tracking and versioning.

    The service implements a complete training pipeline from data loading
    through model deployment, including database interactions, feature
    engineering, model training, evaluation, and registration.

    Attributes:
        db_url (`str`): PostgreSQL connection URI
        mlflow_tracking_uri (`str`): URI for the MLflow tracking server
        labeled_patterns (`dict`): Reference patterns from labeled data
        mlflow_client (`MlflowClient`): Client for MLflow API access
    """

    def __init__(self) -> None:
        """
        Initialise the training service.

        Sets up database and MLflow connections, loads labeled patterns from
        reference data, and initialises the MLflow experiment for tracking.
        Creates a new experiment if one doesn't already exist.

        Raises:
            `Exception`: If MLflow initialisation fails
        """
        self.db_url = config.get_postgres_uri()
        self.mlflow_tracking_uri = config.mlflow_tracking_uri
        self.labeled_patterns = self._load_labeled_patterns()

        try:
            self.mlflow_client = MlflowClient(tracking_uri=self.mlflow_tracking_uri)

            experiments = self.mlflow_client.search_experiments()
            logger.info(f"Available experiments: {[exp.name for exp in experiments]}")

            experiment_name = "Sensor Failure Clustering"

            existing_experiment = None
            for exp in experiments:
                if exp.name == experiment_name:
                    existing_experiment = exp
                    break

            if not existing_experiment:
                logger.info(f"Creating experiment: {experiment_name}")
                self.mlflow_client.create_experiment(experiment_name)

            else:
                logger.info(f"Experiment already exists: {experiment_name}")

            mlflow.set_tracking_uri(self.mlflow_tracking_uri)  # type: ignore
            mlflow.set_experiment(experiment_name)  # type: ignore

        except Exception as err:
            logger.error(f"MLflow initialisation failed: {err}")
            raise

    def _load_labeled_patterns(self) -> dict[float, dict[str, dict[str, float]]]:
        """
        Load labeled failure patterns from CSV file (only once).

        Attempts to load a reference dataset containing labeled failure examples.
        These labeled patterns can be used to compare with the discovered clusters
        and identify the types of failures they represent.

        Returns:
            `dict`: Dictionary of failure patterns with structure
                {failure_type: {sensor_name: {mean, std}}}
                or empty dict if file not found or loading fails
        """
        logger.info(f"Loading labeled data from {config.data_file}")

        if not os.path.exists(config.data_file):
            logger.warning(f"Labeled data file not found: {config.data_file}")
            return {}

        try:
            df = pl.read_csv(config.data_file)
            labeled_df = df.filter(pl.col("Label").is_not_null())
            unique_labels = labeled_df.select("Label").unique()

            logger.info(
                f"Found {labeled_df.height} labeled rows with {unique_labels.height} unique labels"
            )

            sensor_cols = [col for col in df.columns if col.startswith("Sensor")]
            label_patterns = {}

            for label in unique_labels.to_series():
                label_data = labeled_df.filter(pl.col("Label") == label)
                pattern = {}

                for col in sensor_cols:
                    values = label_data.select(col).to_series()
                    pattern[col] = {
                        "mean": float(
                            str(values.mean()) if values.mean() is not None else 0.0
                        ),
                        "std": float(
                            str(values.std()) if values.std() is not None else 0.0
                        ),
                    }

                label_patterns[float(label)] = pattern

            return label_patterns

        except Exception as err:
            logger.error(f"Error loading labeled data: {err}")
            return {}

    async def load_failures(self) -> list[dict[str, Any]]:
        """
        Load failure episodes from the database.

        Queries the database for failure episodes that occurred within the
        configured lookback period. For each failure, loads all associated
        sensor readings chronologically. This data is the basis for the
        clustering algorithm.

        Returns:
            `list[dict[str, Any]]`: List of failure episodes with their readings,
                where each episode contains failure metadata
                and a chronological list of sensor readings
        """
        logger.info("Loading failure data from database")

        lookback_date = datetime.now() - timedelta(hours=config.training_lookback_hours)
        training_end_date = datetime.now()

        failures = await Failure.filter(
            start_time__gte=lookback_date, start_time__lt=training_end_date
        ).prefetch_related("machine", "readings")

        logger.info(f"Found {len(failures)} failure episodes in database")

        failure_episodes = []
        for failure in failures:
            readings_list = await failure.readings.all()  # type: ignore

            readings = sorted(
                cast(list[SensorReading], readings_list), key=lambda r: r.timestamp
            )

            episode_data = []
            for reading in readings:
                values = reading.values_dict
                episode_data.append(values)

            if episode_data:
                failure_episodes.append(
                    {
                        "failure_id": failure.id,
                        "machine_id": failure.machine.machine_id,
                        "start_time": failure.start_time,
                        "readings": episode_data,
                    }
                )

        logger.info(f"Processed {len(failure_episodes)} failure episodes with readings")
        return failure_episodes

    def extract_features(self, failure_episodes: list[dict[str, Any]]) -> pl.DataFrame:
        """
        Extract features from failure episodes for clustering.

        Transforms raw sensor readings into feature vectors suitable for
        clustering. For each sensor, calculates statistical features such as
        mean, standard deviation, minimum, and maximum over the duration of
        the failure episode.

        Args:
            failure_episodes (`list[dict[str, Any]]`): List of failure episodes with readings

        Returns:
            `pl.DataFrame`: DataFrame containing extracted features for each failure episode,
                with one row per episode and columns for each extracted feature
        """
        if not failure_episodes:
            return pl.DataFrame()

        sensor_cols: set[str] = set()
        for episode in failure_episodes:
            for reading in episode["readings"]:
                sensor_cols.update(
                    [k for k in reading.keys() if k.startswith("Sensor")]
                )

        sensor_cols_list = sorted(list(sensor_cols))

        feature_rows = []
        for episode in failure_episodes:
            readings = episode["readings"]
            if not readings:
                continue

            features = {"failure_id": episode["failure_id"]}

            for sensor in sensor_cols_list:
                values = [
                    reading.get(sensor, 0.0)
                    for reading in readings
                    if sensor in reading
                ]

                if values:
                    features[f"{sensor}_mean"] = np.mean(values)
                    features[f"{sensor}_std"] = np.std(values)
                    features[f"{sensor}_min"] = np.min(values)
                    features[f"{sensor}_max"] = np.max(values)

                else:
                    features[f"{sensor}_mean"] = 0.0
                    features[f"{sensor}_std"] = 0.0
                    features[f"{sensor}_min"] = 0.0
                    features[f"{sensor}_max"] = 0.0

            features["duration"] = len(readings)
            feature_rows.append(features)

        return pl.DataFrame(feature_rows)

    def cluster_failures(
        self, features_df: pl.DataFrame
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """
        Cluster failures based on their features.

        Applies K-means clustering to group similar failure episodes based
        on their extracted features. Also calculates a silhouette score to
        evaluate the quality of the clustering. Handles cases where there's
        insufficient data for meaningful clustering.

        Args:
            features_df (`pl.DataFrame`): DataFrame containing extracted features

        Returns:
            `tuple[dict[str, Any] | None, dict[str, Any] | None]`: First element is
                a dictionary mapping failure IDs to cluster labels,
                second element is a dictionary containing the model, scaler,
                number of clusters, and silhouette score.
                Returns `(None, None)` if clustering can't be performed.
        """
        if features_df.is_empty() or features_df.height < config.n_clusters:
            logger.warning("Not enough failure episodes for clustering")
            return None, None

        feature_cols = [col for col in features_df.columns if col != "failure_id"]

        X = features_df.select(feature_cols).to_numpy()
        failure_ids = features_df["failure_id"].to_list()

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        kmeans = KMeans(n_clusters=config.n_clusters, random_state=42)
        labels = kmeans.fit_predict(X_scaled)

        sil_score = 0.0
        if config.n_clusters > 1 and len(X_scaled) > config.n_clusters:
            sil_score = silhouette_score(X_scaled, labels)
            logger.info(f"Silhouette score: {sil_score:.4f}")

        failure_clusters = dict(zip(failure_ids, labels))

        for cluster_id in range(config.n_clusters):
            cluster_size = sum(1 for label in labels if label == cluster_id)
            logger.info(f"Cluster {cluster_id}: {cluster_size} failures")

        return failure_clusters, {
            "model": kmeans,
            "scaler": scaler,
            "n_clusters": config.n_clusters,
            "silhouette_score": sil_score,
        }

    def compare_with_labeled_patterns(
        self, cluster_profiles: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Compare discovered clusters with labeled patterns from CSV.

        For each cluster, calculates similarity scores against known failure
        patterns from labeled data. This helps identify what type of failure
        each cluster represents by finding the closest match in the reference data.

        Args:
            cluster_profiles (`dict[str, Any]`): Dictionary of cluster characteristics

        Returns:
            `dict[str, Any] | None`: Dictionary mapping cluster names to their closest
                matching labeled patterns and similarity scores,
                or `None` if labeled patterns are not available
        """
        if not self.labeled_patterns or not cluster_profiles:
            return None

        results = {}

        for cluster_name, cluster_data in cluster_profiles.items():
            cluster_features = cluster_data["all_features"]

            similarities = {}

            for label, pattern in self.labeled_patterns.items():
                similarity_score = 0
                count = 0

                for sensor, stats in pattern.items():
                    mean_key = f"{sensor}_mean"
                    if mean_key in cluster_features:
                        diff = abs(cluster_features[mean_key] - stats["mean"])
                        if stats["std"] > 0:
                            normalised_diff = diff / stats["std"]
                            similarity_score += 1 / (1 + normalised_diff)
                            count += 1

                if count > 0:
                    similarities[f"label_{label}"] = similarity_score / count

            if similarities:
                most_similar = max(similarities.items(), key=lambda x: x[1])
                results[cluster_name] = {
                    "most_similar_label": most_similar[0],
                    "similarity_score": most_similar[1],
                    "all_similarities": similarities,
                }

        return results

    def analyse_clusters(self, features_df, cluster_labels) -> dict[str, Any]:
        """
        Analyse the characteristics of each cluster.

        Computes the average feature values for each cluster and identifies
        the most distinctive features that characterise each cluster. This
        provides insights into what sensor patterns define each failure type.

        Args:
            features_df (`pl.DataFrame`): DataFrame containing extracted features
            cluster_labels (`dict[str, Any]`): Dictionary mapping failure IDs to cluster labels

        Returns:
            `dict[str, Any]`: Dictionary of cluster profiles with structure
                {cluster_name: {size, distinctive_features, all_features}}
        """
        failure_ids = features_df["failure_id"].to_list()
        clusters = [cluster_labels.get(fid, -1) for fid in failure_ids]
        features_df = features_df.with_columns(
            pl.Series(name="cluster", values=clusters)
        )

        cluster_profiles = {}
        feature_cols = [
            col
            for col in features_df.columns
            if col != "failure_id" and col != "cluster"
        ]

        for cluster_id in set(clusters):
            if cluster_id == -1:
                continue

            cluster_data = features_df.filter(pl.col("cluster") == cluster_id)

            profile = {}
            for col in feature_cols:
                profile[col] = float(cluster_data[col].mean())

            sorted_features = sorted(
                [(col, val) for col, val in profile.items()],
                key=lambda x: abs(x[1]),
                reverse=True,
            )[:5]

            cluster_profiles[f"cluster_{cluster_id}"] = {
                "size": cluster_data.height,
                "distinctive_features": sorted_features,
                "all_features": profile,
            }

        return cluster_profiles

    async def signal_new_model(self, version: str, run_id: str) -> None:
        """
        Signal that a new model version is available.

        Creates a record in the database to notify other services (particularly
        the prediction service) that a new model version is available for use.
        This enables automatic model updating without manual intervention.

        Args:
            version (`str`): Version identifier of the new model
            run_id (`str`): MLflow run ID where the model is stored

        Returns:
            `None`
        """
        try:
            await ModelVersion.create(version=version, run_id=run_id)

            logger.info(f"Signaled new model version {version} with run ID {run_id}")

        except Exception as err:
            logger.error(f"Error signaling new model: {err}")

    async def run(self) -> None:
        """
        Run the complete failure analysis pipeline.

        Executes the entire training workflow from data loading through model
        registration. This is the main entry point for the training process,
        whether triggered directly or through the API. Handles the MLflow run
        lifecycle, artifact logging, and database updates.

        Returns:
            `None`

        Raises:
            `Exception`: If any part of the training pipeline fails
        """
        run_id = None
        try:
            experiment_name = "Sensor Failure Clustering"
            mlflow.set_experiment(experiment_name)  # type: ignore

            logger.info(
                f"Starting MLflow run with tracking URI: {self.mlflow_tracking_uri}"
            )

            with mlflow.start_run(  # type: ignore
                run_name=f"failure_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}"
            ) as run:
                run_id = run.info.run_id
                logger.info(f"Started MLflow run: {run_id}")

                mlflow.set_tag("mlflow.source.name", "sensor_failure_analysis")  # type: ignore
                mlflow.set_tag("mlflow.source.type", "JOB")  # type: ignore

                artifacts_dir = Path("/mlflow/artifacts")
                artifacts_dir.mkdir(parents=True, exist_ok=True)

                logger.info(f"Initialising database with URL: {self.db_url}")
                await init_db(self.db_url)

                logger.info("Loading failure episodes from database")
                failure_episodes = await self.load_failures()

                if not failure_episodes:
                    logger.warning("No failure episodes found")
                    await self.close_db()
                    return None

                logger.info(f"Processing {len(failure_episodes)} failure episodes")
                features_df = self.extract_features(failure_episodes)

                logger.info("Clustering failures")
                failure_clusters, model_info = self.cluster_failures(features_df)

                if failure_clusters and model_info:
                    logger.info("Logging parameters to MLFlow")
                    mlflow.log_param("n_clusters", model_info["n_clusters"])  # type: ignore
                    mlflow.log_param("n_failures", len(failure_clusters))  # type: ignore
                    mlflow.log_param(  # type: ignore
                        "training_lookback_hours", config.training_lookback_hours
                    )

                    logger.info("Analysing clusters")
                    cluster_profiles = self.analyse_clusters(
                        features_df, failure_clusters
                    )
                    comparison_results = self.compare_with_labeled_patterns(
                        cluster_profiles
                    )

                    if comparison_results:
                        logger.info(
                            "Adding label comparison results to cluster profiles"
                        )
                        for cluster_name, comparison in comparison_results.items():
                            if cluster_name in cluster_profiles:
                                cluster_profiles[cluster_name]["label_comparison"] = (
                                    comparison
                                )

                    logger.info("Writing cluster profiles to JSON file")
                    profiles_path = artifacts_dir / "profiles.json"
                    with profiles_path.open("w") as f:
                        json.dump(cluster_profiles, f, indent=2)

                    logger.info("Logging artifacts to MLFlow")
                    mlflow.log_artifact(str(profiles_path))  # type: ignore

                    kmeans_model = model_info["model"]
                    scaler = model_info["scaler"]
                    silhouette_score_value = model_info["silhouette_score"]

                    feature_cols = [
                        col for col in features_df.columns if col != "failure_id"
                    ]
                    X = features_df.select(feature_cols).to_numpy()

                    logger.info("Logging model to MLFlow")
                    mlflow.sklearn.log_model(  # type: ignore
                        kmeans_model,
                        "kmeans_model",
                        registered_model_name="sensor_failure_clustering",
                        input_example=X[0:1],
                    )

                    logger.info("Saving scaler to pickle file")
                    scaler_path = artifacts_dir / "scaler.pkl"
                    with scaler_path.open("wb") as f:
                        pickle.dump(scaler, f)

                    logger.info("Logging scaler to MLFlow")
                    mlflow.log_artifact(str(scaler_path))  # type: ignore

                    logger.info(f"Logging silhouette score: {silhouette_score_value}")
                    mlflow.log_metric("silhouette_score", silhouette_score_value)  # type: ignore

                    logger.info("Getting MLFlow client for model version management")
                    client = MlflowClient()

                    registered_model_info = client.search_model_versions(
                        "name='sensor_failure_clustering'"
                    )

                    if registered_model_info:
                        model_version = registered_model_info[0].version

                        try:
                            logger.info(
                                f"Setting 'production' alias for model version {model_version}"
                            )
                            client.set_registered_model_alias(
                                name="sensor_failure_clustering",
                                alias="production",
                                version=model_version,
                            )

                        except Exception as err:
                            logger.warning(f"Could not set model alias: {err}")

                        logger.info(f"Model registered with version {model_version}")

                        try:
                            logger.info("Creating cluster record in database")
                            model_record = await Cluster.create(
                                mlflow_run_id=run_id,
                                mlflow_model_version=model_version,
                                n_clusters=model_info["n_clusters"],
                                silhouette_score=model_info["silhouette_score"],
                                cluster_profiles=cluster_profiles,
                                is_active=True,
                            )

                            logger.info("Setting previous cluster models as inactive")
                            await Cluster.filter(id__not=model_record.id).update(
                                is_active=False
                            )

                            await self.signal_new_model(model_version, run_id)

                            logger.info(
                                f"Completed clustering with {model_info['n_clusters']} clusters"
                            )
                            logger.info(
                                f"Model saved to database with ID: {model_record.id}"
                            )

                        except Exception as err:
                            logger.error(
                                f"Error saving cluster model to database: {str(err)}"
                            )

                    await self.close_db()

                else:
                    logger.warning(
                        "Clustering failed - insufficient data or invalid parameters"
                    )
                    await self.close_db()

                logger.info(f"MLflow run {run_id} completed successfully")

        except Exception as err:
            logger.error(f"Analysis failed: {str(err)}")
            logger.error(traceback.format_exc())

            try:
                await self.close_db()

            except Exception as err:
                logger.error(f"Error closing database: {err}")

            if run_id:
                try:
                    mlflow.end_run(status="FAILED")  # type: ignore

                except Exception as err:
                    logger.error(f"Could not end run: {err}")

            raise

    async def close_db(self) -> None:
        """
        Close database connection.

        Gracefully closes all active database connections to ensure proper
        resource cleanup. This is typically called at the end of a training
        run or when an error occurs.

        Returns:
            `None`
        """
        await Tortoise.close_connections()
