"""
Job status monitoring utilities for the Airflow DAGs.

This module provides functions to check the status of training jobs
and determine when they have completed or failed. It uses the Airflow
context to retrieve job IDs and connection information.
"""

import requests

from airflow.hooks.base import BaseHook


def check_status(**context) -> bool:
    """
    Check the status of a training job with robust error handling.

    This function retrieves the job ID from the previous task using XCom,
    then queries the trainer API for the job status. It handles various
    error conditions that might occur during the status check.

    Args:
        **context: The Airflow task context containing task instance (ti)
            and other runtime information

    Returns:
        bool: `True` if the job has completed or failed, `False` otherwise
            or if an error occurred during the status check
    """
    conn = BaseHook.get_connection("trainer_api")
    base_url = conn.host

    job_id = context["ti"].xcom_pull(task_ids="trigger_training")["job_id"]

    try:
        status_url = f"{base_url.rstrip('/')}/api/train/{job_id}"
        response = requests.get(status_url, timeout=10)

        if response.status_code == 200:
            status_data = response.json()
            print(f"Job status: {status_data}")

            return status_data["status"] in ["completed", "failed"]

        else:
            print(f"Unexpected status code: {response.status_code}")
            return False

    except Exception as err:
        print(f"Error checking training status: {str(err)}")
        return False
