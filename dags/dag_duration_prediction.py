from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from typing import Dict, Any
import pendulum

LOCAL_TZ = pendulum.timezone("Europe/London")

dag_args = {
    "depends_on_past": False,
    "email": ["yezerg@gmail.com"],
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function, # or list of functions
    # 'on_success_callback': some_other_function, # or list of functions
    # 'on_retry_callback': another_function, # or list of functions
    # 'sla_miss_callback': yet_another_function, # or list of functions
    # 'trigger_rule': 'all_success'
}


dag = DAG(
    "duration_prediction_training",
    description="This dag trains the duration prediction model",
    default_args=dag_args,
    schedule="31 12 * * *",  # This is a cron expression that schedules the DAG to run daily at 12:31 PM
    start_date=datetime(2020, 1, 1, tzinfo=LOCAL_TZ),
    catchup=False,
    tags=["mlops"],
    params={
        "DURATION_PREDICTION_SCRIPT_PATH": "/home/yezer/projects/mlops-zoomcamp/03-orchestration/duration-prediction.py",
        "VENV_PATH": "/home/yezer/projects/mlops-zoomcamp",
        "YEAR": 2021,
        "MONTH": 1
        }
)

def tarea_func(**kwargs: Any) -> Dict[str, str]:
    print("You are welcome to this workflow!")
    return {"tarea0": "ok"}

tarea0 = PythonOperator(task_id="tarea0", python_callable=tarea_func, dag=dag)

tarea1 = BashOperator(
    task_id="tarea1",
    bash_command="""
        source {{params.VENV_PATH}}/.venv/bin/activate
        python {{params.DURATION_PREDICTION_SCRIPT_PATH}} --month {{ params.MONTH }} --year {{ params.YEAR }}
    """,
    dag=dag)

tarea0 >> tarea1