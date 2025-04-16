import polars as pl
from loguru import logger


def calculate_sensor_statistics(df: pl.DataFrame) -> dict[str, dict[str, float]]:
    """
    Calculate statistics for each sensor column in the dataset.

    Args:
        df (pl.DataFrame): Polars DataFrame containing sensor data

    Returns:
        dict: Dictionary of sensor statistics with structure {sensor_name: {mean, std, min, max}}
    """
    sensor_stats = {}
    sensor_cols = [col for col in df.columns if col.startswith("Sensor")]

    # Calculate statistics for normal sensor behaviour
    for col in sensor_cols:
        stats = df.select(
            [
                pl.col(col).mean().alias("mean"),
                pl.col(col).std().alias("std"),
                pl.col(col).min().alias("min"),
                pl.col(col).max().alias("max"),
            ]
        ).row(0)

        sensor_stats[col] = {
            "mean": float(stats["mean"]),
            "std": float(stats["std"]),
            "min": float(stats["min"]),
            "max": float(stats["max"]),
        }

    return sensor_stats


def analyze_failure_patterns(
    df: pl.DataFrame,
) -> dict[float, dict[str, dict[str, float]]]:
    """
    Analyze patterns for each failure type in the dataset.

    Args:
        df (pl.DataFrame): Polars DataFrame containing sensor data with failure labels

    Returns:
        dict: Dictionary of failure patterns with structure {failure_type: {sensor_name: {mean, std}}}
    """
    failure_patterns: dict[float, dict[str, dict[str, float]]] = {}
    sensor_cols = [col for col in df.columns if col.startswith("Sensor")]

    # Filter rows with Label values
    labeled_data = df.filter(pl.col("Label").is_not_null())

    # If no labeled data, return empty dictionary
    if labeled_data.height == 0:
        logger.warning("No labeled failure data found")
        return failure_patterns

    # Get unique labels
    labels = labeled_data.select("Label").unique().to_series().to_list()

    for label in labels:
        label_data = labeled_data.filter(pl.col("Label") == label)
        failure_patterns[label] = {}

        for col in sensor_cols:
            stats = label_data.select(
                [pl.col(col).mean().alias("mean"), pl.col(col).std().alias("std")]
            ).row(0)

            failure_patterns[label][col] = {
                "mean": float(stats["mean"]),
                "std": float(stats["std"]),
            }

    logger.info(
        f"Analyzed {labeled_data.height} labeled data points with {len(labels)} failure types"
    )
    return failure_patterns


def get_default_sensor_statistics(num_sensors: int = 20) -> dict[str, dict[str, float]]:
    """
    Generate default sensor statistics when data is unavailable.

    Args:
        num_sensors (int): Number of sensors to generate statistics for

    Returns:
        dict: Dictionary of default sensor statistics
    """
    sensor_stats = {}
    for i in range(num_sensors):
        col = f"Sensor {i}"
        sensor_stats[col] = {"mean": 0.0, "std": 1.0, "min": -1.0, "max": 1.0}

    return sensor_stats


def get_default_failure_patterns(
    num_sensors: int = 20,
) -> dict[float, dict[str, dict[str, float]]]:
    """
    Generate default failure patterns when data is unavailable.

    Args:
        num_sensors (int): Number of sensors to include in failure patterns

    Returns:
        dict: Dictionary of default failure patterns
    """
    return {
        1.0: {f"Sensor {i}": {"mean": 0.8, "std": 0.3} for i in range(num_sensors)},
        2.0: {f"Sensor {i}": {"mean": -0.8, "std": 0.3} for i in range(num_sensors)},
        3.0: {f"Sensor {i}": {"mean": 0.0, "std": 2.0} for i in range(num_sensors)},
    }


def analyse_dataset(
    data_file: str,
    num_sensors: int = 20,
) -> tuple[dict[str, dict[str, float]], dict[float, dict[str, dict[str, float]]]]:
    """
    Load and analyze the sensor dataset to extract patterns and statistics.

    Args:
        data_file (str): Path to the CSV data file
        num_sensors (int): Number of sensors expected in the data

    Returns:
        tuple: (sensor_stats, failure_patterns) containing the analyzed data
    """
    try:
        # Load dataset using Polars
        df = pl.read_csv(data_file)
        logger.info(f"Loaded dataset with {df.height} rows")

        # Calculate sensor statistics and failure patterns
        sensor_stats = calculate_sensor_statistics(df)
        failure_patterns = analyze_failure_patterns(df)

        return sensor_stats, failure_patterns

    except Exception as err:
        logger.error(f"Error analyzing dataset: {err}")
        return get_default_sensor_statistics(num_sensors), get_default_failure_patterns(
            num_sensors
        )
