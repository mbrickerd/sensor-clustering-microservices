# Grafana

This directory contains the Grafana configuration for the Sensor Failure Detection System. Grafana provides visualisation and monitoring dashboards for sensor data, model performance, and system metrics.

**Table of contents**
- [Grafana](#grafana)
  - [Overview](#overview)
  - [Directory Structure](#directory-structure)
  - [Configuration Files](#configuration-files)
  - [Dashboards](#dashboards)
  - [Data Sources](#data-sources)
  - [Integration with Microservices](#integration-with-microservices)
  - [Environment Variables](#environment-variables)
  - [Accessing Grafana](#accessing-grafana)
  - [Troubleshooting](#troubleshooting)

## Overview

The Grafana component provides real-time monitoring and visualisation for the Sensor Failure Detection System. It offers:
- Interactive dashboards for ML model performance
- Sensor failure detection monitoring
- Prediction metrics and drift detection visualisation
- System health monitoring across all services

## Directory Structure

```
grafana/
├── provisioning/
│   ├── dashboards/
│   │   ├── dashboard.yml       # Dashboard provider configuration
│   │   └── monitoring.json     # Sensor clustering dashboard
│   └── datasources/
│       └── datasource.yml      # Prometheus data source configuration
└── README.md                   # This documentation file
```

## Configuration Files

### Dashboard Provider (`dashboard.yml`)

This file configures how Grafana discovers and loads dashboards:

```yaml
apiVersion: 1

providers:
  - name: "Model Monitoring"
    orgId: 1
    folder: ""
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: true
```

### Data Source Configuration (`datasource.yml`)

This file configures Prometheus as the primary data source:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    version: 1
    editable: true
    uid: prometheus
    jsonData:
      timeInterval: "15s"
      httpMethod: "POST"
```

## Dashboards

The `monitoring.json` file defines a comprehensive dashboard for the sensor clustering and prediction system with the following panels:

1. **Prediction Activity** - Real-time prediction rate per minute
2. **Total Predictions** - Cumulative count of predictions made
3. **Data Drift Detection** - Current drift score with thresholds
4. **Prediction Latency** - Performance metrics with percentiles
5. **Drift Score Over Time** - Trend analysis for data drift
6. **Predictions by Cluster** - Distribution of predictions across clusters
7. **Prediction Rate by Cluster** - Time series of prediction rates by cluster

The dashboard includes:
- Variable templates for data source selection
- Time range controls for different analysis periods
- Thresholds and color coding for key metrics
- Multiple visualisation types (gauge, pie chart, time-series)

## Data Sources

Grafana connects to the following data sources:

1. **Prometheus** - Primary time-series database for metrics
   - Collects custom metrics from the `sensor-predictor` service
   - Stores system metrics from all containers
   - Provides query capabilities for dashboard visualisations

## Integration with Microservices

Grafana integrates with several components in the system:

1. **Prometheus** - Collects and stores all metrics data that Grafana visualises
   - Located at `http://prometheus:9090`
   - Configured as the default data source

2. **Sensor Predictor** - Exposes custom metrics about model predictions
   - Metrics exposed on port 8001
   - Includes prediction counts, latency, and drift detection scores

3. **Exporters** - Additional metric collection services
   - `kafka-exporter`: Provides Kafka metrics
   - `postgres-exporter`: Provides PostgreSQL metrics

The metrics flow follows this pattern:
1. Services expose metrics endpoints (Prometheus format)
2. Prometheus scrapes these endpoints at regular intervals
3. Grafana queries Prometheus and visualises the data

## Environment Variables

The Grafana service uses the following environment variables in `docker-compose.yml`:

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `GF_SECURITY_ADMIN_USER` | Admin username | admin |
| `GF_SECURITY_ADMIN_PASSWORD` | Admin password | admin |
| `GF_USERS_ALLOW_SIGN_UP` | Allow user registration | false |
| `GF_AUTH_ANONYMOUS_ENABLED` | Enable anonymous access | true |
| `GF_AUTH_ANONYMOUS_ORG_ROLE` | Role for anonymous users | Viewer |

These variables are configured in the `docker-compose.yml` file:

```yaml
environment:
  - GF_SECURITY_ADMIN_USER=${GRAFANA_USER:-admin}
  - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
  - GF_USERS_ALLOW_SIGN_UP=false
  - GF_AUTH_ANONYMOUS_ENABLED=true
  - GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
```

## Accessing Grafana

Grafana is accessible through your web browser:

- **URL**: http://localhost:3000
- **Default username**: admin (or value of `GRAFANA_USER`)
- **Default password**: admin (or value of `GRAFANA_PASSWORD`)

The main dashboard, "Sensor Clustering Monitoring", is automatically provisioned and available immediately after startup.

## Troubleshooting

Common issues and their solutions:

1. **Dashboard not showing any data**
   - Check if Prometheus is running: `docker ps | grep prometheus`
   - Verify the data source is configured correctly in Grafana
   - Ensure the `sensor-predictor` service is exposing metrics
   - Check Prometheus targets: http://localhost:9090/targets

2. **Missing metrics in dashboard**
   - Check if the metric names in the dashboard match those exposed by services
   - Verify the `sensor-predictor` service is generating predictions
   - Check Prometheus logs: `docker logs prometheus`

3. **Authentication issues**
   - Reset admin password using Docker:
     ```
     docker exec -it grafana grafana-cli admin reset-admin-password newpassword
     ```
   - Check environment variables are correctly set in `docker-compose.yml`

4. **Dashboard not loading**
   - Verify the dashboard JSON is valid
   - Check Grafana logs: `docker logs grafana`
   - Ensure the dashboard provider configuration is correct
