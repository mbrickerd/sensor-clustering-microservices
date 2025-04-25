import json
from datetime import timedelta

import pendulum

from airflow import DAG  # type: ignore
from airflow.operators.python import PythonOperator
from airflow.providers.http.operators.http import HttpOperator
from dags.utils.healthcheck import mlflow_healthcheck, trainer_healthcheck
from dags.utils.status import check_status

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(seconds=30),
    "start_date": pendulum.now("Europe/Berlin").subtract(hours=1),
}


with DAG(
    "train_clustering_model",
    default_args=default_args,
    description="Train sensor failure clustering model every hour",
    schedule_interval="@hourly",
    catchup=False,
    is_paused_upon_creation=False,
    tags=["sensor", "ml", "training"],
) as dag:
    check_mlflow = PythonOperator(
        task_id="check_mlflow_health",
        python_callable=mlflow_healthcheck,
    )

    check_trainer = PythonOperator(
        task_id="check_trainer_health",
        python_callable=trainer_healthcheck,
    )

    trigger = HttpOperator(
        task_id="trigger_training",
        http_conn_id="trainer_api",
        endpoint="/api/train",
        method="POST",
        headers={"Content-Type": "application/json"},
        response_filter=lambda response: json.loads(response.text),
        log_response=True,
    )

    monitor = PythonOperator(
        task_id="monitor_training",
        python_callable=check_status,
        provide_context=True,
        retries=3,
        retry_delay=timedelta(seconds=30),
    )

    check_mlflow >> check_trainer >> trigger >> monitor
