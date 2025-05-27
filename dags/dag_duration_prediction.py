from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, Any

# Add the directory containing the duration-prediction.py script to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from duration_prediction import run

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_training(**context: Dict[str, Any]) -> None:
    # Get the execution date from the context
    execution_date = context['execution_date']
    year = execution_date.year
    month = execution_date.month
    
    # Run the training script
    run(year=year, month=month)

with DAG(
    'duration_prediction_training',
    default_args=default_args,
    description='Train duration prediction model',
    schedule_interval='0 0 1 * *',  # Run at midnight on the first day of each month
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=['mlops'],
) as dag:

    # Run the training using the existing virtual environment
    train_model = BashOperator(
        task_id='train_model',
        bash_command="""
            source .venv/bin/activate
            python duration_prediction.py --year {{ execution_date.year }} --month {{ execution_date.month }}
        """
    ) 