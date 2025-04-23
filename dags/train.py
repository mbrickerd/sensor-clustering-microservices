from airflow import DAG
from airflow.providers.http.operators.http import HttpOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.http_sensor import HttpSensor
import json
import pendulum
from datetime import timedelta

from dags.utils.healthcheck import mlflow_healthcheck, trainer_healthcheck
from dags.utils.status import check_status

# Set start date to a time in the recent past
start_date = pendulum.now('Europe/Berlin').subtract(minutes=5)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(seconds=30),
    'start_date': start_date,
}

def check_training_status(**context):
    """
    Custom function to check training status with more robust error handling
    """
    from airflow.hooks.base import BaseHook
    import requests
    
    # Retrieve the connection
    conn = BaseHook.get_connection('trainer_api')
    base_url = conn.host
    
    # Get the job ID from the previous task
    job_id = context['ti'].xcom_pull(task_ids='trigger_training')['job_id']
    
    try:
        # Construct the full URL
        status_url = f"{base_url.rstrip('/')}/api/train/{job_id}"
        
        # Make the request
        response = requests.get(status_url, timeout=10)
        
        # Check if the request was successful
        if response.status_code == 200:
            status_data = response.json()
            print(f"Job status: {status_data}")
            
            # Return True if job is completed or failed
            return status_data['status'] in ['completed', 'failed']
        else:
            print(f"Unexpected status code: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"Error checking training status: {str(e)}")
        return False

with DAG(
    'train_clustering_model',
    default_args=default_args,
    description='Train sensor failure clustering model every 5 minutes',
    schedule_interval='*/5 * * * *',
    catchup=False,
    is_paused_upon_creation=False,
    tags=['sensor', 'ml', 'training'],
) as dag:

    # Health checks with direct function calls
    check_mlflow = PythonOperator(
        task_id='check_mlflow_health',
        python_callable=mlflow_healthcheck, 
    )
    
    check_trainer = PythonOperator(
        task_id='check_trainer_health',
        python_callable=trainer_healthcheck,
    )
    
    # Trigger training via HTTP
    trigger = HttpOperator(
        task_id='trigger_training',
        http_conn_id='trainer_api',
        endpoint='/api/train',
        method='POST',
        headers={"Content-Type": "application/json"},
        response_filter=lambda response: json.loads(response.text),
        log_response=True,
    )
    
    # Monitor training status with a custom Python operator
    monitor = PythonOperator(
        task_id='monitor_training',
        python_callable=check_status,
        provide_context=True,
        retries=3,
        retry_delay=timedelta(seconds=30),
    )

    # Define task dependencies
    check_mlflow >> check_trainer >> trigger >> monitor