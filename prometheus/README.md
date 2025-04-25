# Prometheus

This directory contains the Prometheus configuration for the Sensor Failure Detection System. Prometheus provides metrics collection, storage, and alerting capabilities for monitoring all services.

**Table of contents**
- [Prometheus](#prometheus)
  - [Overview](#overview)
  - [Directory Structure](#directory-structure)
  - [Configuration File](#configuration-file)
  - [Metrics Collection](#metrics-collection)
  - [Integration with Microservices](#integration-with-microservices)
  - [Query Interface](#query-interface)
  - [Grafana Integration](#grafana-integration)
  - [Retention and Storage](#retention-and-storage)
  - [Troubleshooting](#troubleshooting)

## Overview

The Prometheus component is responsible for metrics collection and monitoring across the Sensor Failure Detection System:
- Collects metrics from all services via HTTP endpoints
- Provides a time-series database for metrics storage
- Supports PromQL for querying and analysing metrics
- Integrates with Grafana for visualisation
- Enables monitoring of system health and performance
- Tracks custom metrics for ML model evaluation

## Directory Structure

```
prometheus/
├── prometheus.yml          # Main Prometheus configuration
└── README.md               # This documentation file
```

## Configuration File

The `prometheus.yml` file defines how Prometheus collects metrics:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "sensor-predictor"
    static_configs:
      - targets: ["sensor-predictor:8001"]
    metrics_path: "/metrics"

  - job_name: "kafka-exporter"
    static_configs:
      - targets: ["kafka-exporter:9308"]

  - job_name: "postgres-exporter"
    static_configs:
      - targets: ["postgres-exporter:9187"]
```

Key configuration settings:
- **Global settings**:
  - `scrape_interval`: How frequently metrics are collected (15 seconds)
  - `evaluation_interval`: How frequently alerting rules are evaluated

- **Scrape configurations**:
  - Each job defines a target service to monitor
  - Targets are specified by hostname and port
  - The metrics path defaults to `/metrics`

## Metrics Collection

Prometheus collects metrics from these sources:

1. **Prometheus itself** (`localhost:9090`)
   - Internal metrics about Prometheus performance
   - Scrape durations, sample counts, etc.

2. **Sensor Predictor** (`sensor-predictor:8001`)
   - ML prediction metrics
   - Prediction counts and latencies
   - Cluster distributions
   - Drift detection scores

3. **Kafka Exporter** (`kafka-exporter:9308`)
   - Kafka broker metrics
   - Topic and partition statistics
   - Consumer group lag
   - Message throughput

4. **PostgreSQL Exporter** (`postgres-exporter:9187`)
   - Database performance metrics
   - Connection counts
   - Query statistics
   - Table and index sizes

## Integration with Microservices

Prometheus integrates with several components in the system:

1. **Sensor Predictor Service**
   - Exposes custom metrics via Prometheus client
   - Tracks prediction counts, latency, and drift
   - Provides input for Grafana dashboards

2. **Kafka Exporter**
   - Integrates with Kafka to expose broker metrics
   - Monitors message flow from producer to consumer
   - Helps identify backpressure issues

3. **Postgres Exporter**
   - Monitors the PostgreSQL database
   - Tracks query performance and resource usage
   - Provides early warning of database issues

4. **Grafana**
   - Uses Prometheus as a data source
   - Visualises collected metrics in dashboards
   - Creates alerts based on metric thresholds

## Query Interface

Prometheus provides a web interface accessible at http://localhost:9090 with:

- **Expression Browser**: For running PromQL queries
- **Graph View**: For visualising time-series data
- **Targets Page**: Shows scrape target status
- **Alerts Page**: Displays configured alerts
- **Status Page**: Shows Prometheus configuration

Common useful PromQL queries:

```
# Prediction rate per minute
rate(sensor_predictions_total[1m]) * 60

# 95th percentile prediction latency
histogram_quantile(0.95, rate(sensor_prediction_latency_seconds_bucket[5m]))

# Current drift score
sensor_drift_score

# Prediction counts by cluster
sensor_predictions_by_cluster

# Kafka consumer lag
kafka_consumergroup_lag_sum
```

## Grafana Integration

Prometheus serves as the primary data source for Grafana dashboards:

- Grafana queries Prometheus using PromQL
- Metrics are visualised in the "Sensor Clustering Monitoring" dashboard
- Time-series data shows trends and patterns
- Thresholds highlight potential issues
- Variables allow filtering by time range or metric

The connection is configured in Grafana's data source configuration:
```yaml
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

## Retention and Storage

Prometheus is configured with the following storage settings:

```
--storage.tsdb.path=/prometheus
--storage.tsdb.retention.time=15d
--storage.tsdb.min-block-duration=2h
```

These settings mean:
- Metrics are stored in the `/prometheus` directory (mounted as a volume)
- Data is retained for 15 days
- Block compression occurs in 2-hour chunks
- Data is stored in a time-series database (TSDB) format

## Troubleshooting

Common issues and their solutions:

1. **Missing metrics**
   - Check that the target service is running
   - Verify the service is exposing metrics on the correct port
   - Check Prometheus targets page for scrape errors
   - Look for network issues between containers

2. **Service showing as "down"**
   - Check if the service is healthy
   - Verify prometheus.yml has correct target configuration
   - Test endpoint manually: `curl http://service:port/metrics`
   - Check service logs for errors

3. **High cardinality issues**
   - Look for metrics with too many labels
   - Monitor Prometheus memory usage
   - Consider aggregating metrics with high cardinality
   - Adjust scrape interval if necessary

4. **Storage issues**
   - Check available disk space
   - Monitor the size of the TSDB volume
   - Consider adjusting retention period
   - Remove unused metrics to reduce storage requirements
