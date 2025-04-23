import requests
from airflow.hooks.base import BaseHook


def check_status(**context) -> bool:
    """
    Custom function to check training status with robust error handling
    """
    # Retrieve the connection
    conn = BaseHook.get_connection('trainer_api')
    
    # Make sure we have the proper URL scheme
    if hasattr(conn, 'host') and conn.host:
        if conn.host.startswith('http://') or conn.host.startswith('https://'):
            base_url = conn.host.rstrip('/')
        else:
            base_url = f"http://{conn.host.rstrip('/')}"
    else:
        # Fallback to environment variable or default
        base_url = "http://sensor-trainer:8000"
    
    # Get the job ID from the previous task
    job_id = context['ti'].xcom_pull(task_ids='trigger_training')['job_id']
    
    try:
        # Construct the full URL
        status_url = f"{base_url}/api/train/{job_id}"
        
        print(f"Checking status URL: {status_url}")
        
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
    
    except Exception as err:
        print(f"Error checking training status: {str(err)}")
        return False