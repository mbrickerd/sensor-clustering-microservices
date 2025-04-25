# ML-Powered Sensor Data Analysis Platform

A microservices-based platform for collecting, storing, analysing and predicting machine failures from sensor data streams.

**Table of contents**
- [ML-Powered Sensor Data Analysis Platform](#ml-powered-sensor-data-analysis-platform)
  - [Architecture Overview](#architecture-overview)
  - [Components](#components)
    - [Data Pipeline](#data-pipeline)
    - [ML Pipeline](#ml-pipeline)
    - [Monitoring & Observability](#monitoring--observability)
  - [Environment Variables](#environment-variables)
  - [Prerequisites](#prerequisites)
  - [Tooling](#tooling)
    - [uv](#uv)
    - [direnv (optional)](#direnv-optional)
  - [Getting Started](#getting-started)
    - [Local Development](#local-development)
    - [Docker Deployment](#docker-deployment)
  - [Project Structure](#project-structure)
  - [Development Guide](#development-guide)
    - [Adding New Sensors](#adding-new-sensors)
    - [Modifying ML Models](#modifying-ml-models)
    - [Extending Failure Analysis](#extending-failure-analysis)
  - [Contributing](#contributing)

## Architecture Overview

This platform implements a complete end-to-end solution for sensor data processing and machine failure analysis. The system follows a microservices architecture pattern with the following main components:

- Kafka-based message streaming
- PostgreSQL for data persistence
- Machine learning models for failure clustering and prediction
- MLflow for experiment tracking
- Monitoring stack with Prometheus and Grafana

## Components

### Data Pipeline

- **Producer**: Simulates sensor data from machines and publishes to Kafka
- **Consumer**: Consumes sensor data from Kafka and persists to PostgreSQL
- **Domain**: Shared data models and database schema definitions

### ML Pipeline

- **Trainer**: Periodically trains clustering models on historical failure data
- **Predictor**: Uses trained models to predict and detect anomalies
- **MLflow**: Tracks model versions, parameters and metrics

### Monitoring & Observability

- **Prometheus**: Collects metrics from all services
- **Grafana**: Visualizes metrics in customizable dashboards

## Environment Variables

The platform uses environment variables for configuration. These can be set directly or via a `.env` file with direnv.

| Environment Variable       | Description                                           | Default Value               |
|----------------------------|-------------------------------------------------------|----------------------------|
| `KAFKA_BOOTSTRAP_SERVERS`  | Kafka broker address                                  | `localhost:9092`           |
| `KAFKA_TOPIC`              | Topic for sensor readings                             | `machine.sensor.readings`  |
| `KAFKA_GROUP_ID`           | Consumer group ID                                     | `sensor-consumer-group`    |
| `POSTGRES_HOST`            | PostgreSQL host                                       | `localhost`                |
| `POSTGRES_PORT`            | PostgreSQL port                                       | `5432`                     |
| `POSTGRES_USER`            | PostgreSQL username                                   | `sensor_user`              |
| `POSTGRES_PASSWORD`        | PostgreSQL password                                   | `sensor_password`          |
| `POSTGRES_DB`              | PostgreSQL database name                              | `sensor_data`              |
| `MLFLOW_TRACKING_URI`      | MLflow tracking server URI                            | `http://mlflow:5000`       |
| `SIMULATION_INTERVAL_MS`   | Interval between sensor data generation (ms)          | `500`                      |
| `NUM_SENSORS`              | Number of sensors per machine                         | `20`                       |
| `BATCH_SIZE`               | Batch size for DB operations                          | `100`                      |
| `COMMIT_INTERVAL_MS`       | Kafka auto-commit interval                            | `5000`                     |
| `PGADMIN_DEFAULT_EMAIL`    | pgAdmin login email                                   | -                          |
| `PGADMIN_PASSWORD`         | pgAdmin login password                                | -                          |
| `TRAINING_LOOKBACK_HOURS`  | Hours of historical data to use for training          | `1`                        |

## Prerequisites

- [**Python 3.12+**](https://www.python.org/downloads/)
- [**Docker**](https://docs.docker.com/get-docker/) and [**Docker Compose**](https://docs.docker.com/compose/install/)
- [**uv**](https://docs.astral.sh/uv/) (for dependency management)
- [**direnv**](https://direnv.net/) (optional, but recommended)

## Tooling

### uv

This repository uses `uv` as a package manager to ensure consistent dependency versions. Please follow the [official documentation](https://docs.astral.sh/uv/getting-started/installation/) on installing uv on your system.

After installing `uv`, you can install the required packages for each component by running the following command in the component's directory:

```bash
cd <component-directory>  # e.g., cd consumer
uv sync --dev
```

### direnv (optional)

For setting up environment variables, you can use `direnv` to automatically load these from a `.envrc` file. This makes working with the various services easier, as the environment is automatically configured when you navigate to the project directory.

To enable `direnv` for the first time after creating a `.envrc` file, run:

```bash
direnv allow .
```

To validate that environment variables are loaded correctly:

```bash
env | grep KAFKA
```

## Getting Started

### Local Development

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Create a `.envrc` file with your environment variables:
   ```bash
   cp .envrc.example .envrc
   # Edit .envrc with your settings
   direnv allow .
   ```

3. Start the infrastructure services:
   ```bash
   docker compose up -d zookeeper kafka postgres
   ```

4. Install dependencies for the component you're working on:
   ```bash
   cd <component-directory>  # e.g., cd consumer
   uv sync --dev
   ```

5. Run the component:
   ```bash
   python -m <component>.app  # e.g., python -m consumer.app
   ```

### Docker Deployment

To deploy the complete system using Docker Compose:

```bash
docker compose up -d
```

To view logs for a specific service:

```bash
docker compose logs -f <service-name>  # e.g., docker compose logs -f sensor-consumer
```

Access the web interfaces:
- Kafka UI: http://localhost:8080
- pgAdmin: http://localhost:5050
- MLflow: http://localhost:5000
- Grafana: http://localhost:3000

## Project Structure

```
.
├── consumer/          # Kafka consumer service
├── producer/          # Sensor data producer service
├── domain/            # Shared data models
├── trainer/           # ML model training service
├── predictor/         # ML model inference service
├── mlflow/            # MLflow configuration
├── grafana/           # Grafana dashboards
├── prometheus/        # Prometheus configuration
├── docker-compose.yml # Docker Compose configuration
└── data/              # Sample data directory
```

Each component follows a similar structure:
- `app.py`: Main entry point
- `config.py`: Configuration loader
- `services/`: Business logic
- `models/`: Data models
- `utils/`: Utility functions

## Development Guide

### Adding New Sensors

1. Update the `NUM_SENSORS` environment variable
2. Modify `producer/utils/analysis.py` to include statistical properties
3. Ensure the consumer can handle the additional sensor data fields

### Modifying ML Models

1. Update the clustering algorithm in `trainer/services/trainer.py`
2. Test with historical data before deployment
3. Verify MLflow is tracking the new model parameters

### Extending Failure Analysis

1. Add new failure patterns in `producer/utils/analysis.py`
2. Update the pattern detection logic in `trainer/services/trainer.py`
3. Modify the database schema if necessary

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

When contributing:
- Follow the project's code style
- Add tests for new features
- Update documentation as needed
