"""
Airflow DAGs for the Sensor Failure Detection System.

This package contains the Directed Acyclic Graphs (DAGs) that orchestrate
the machine learning workflows for the Sensor Failure Detection System.
The DAGs schedule and manage training jobs, perform health checks on
dependent services, and monitor job progress.

The package includes:
- Training DAG for clustering model generation
- Utility functions for service health verification
- Job status monitoring utilities
"""
