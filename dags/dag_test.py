from datetime import datetime, timedelta
from typing import Any

import pendulum

from airflow import DAG
from airflow.exceptions import AirflowFailException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

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

local_tz = pendulum.timezone("Europe/London")

dag = DAG(
    "test1",
    description="dag_test",
    default_args=dag_args,
    schedule="31 12 * * *",  # This is a cron expression that schedules the DAG to run daily at 12:28 PM
    start_date=datetime(2020, 1, 1, tzinfo=local_tz),
    catchup=False,
    tags=["tests"],
    params={"commit": "000000"},  # esto añade parámetros a la DAG, que podemso meter externamente.
)


def tarea0_func(**kwargs: Any) -> dict[str, int]:
    dag_run: Any = kwargs["dag_run"]
    conf: dict[str, Any] = dag_run.conf  # así accedo a los parámetros de mi DAG

    # si commit está en la descripción, y es igual 1, hoy no desplegamos.
    if "commit" in conf and conf["commit"] == "1":
        raise AirflowFailException("Hoy no desplegamos porque no me gusta el commit 1!")

    return {"ok": 1}


def tarea2_func(**kwargs: Any) -> dict[str, int]:
    ti: Any = kwargs["ti"]
    xcom_value: Any = ti.xcom_pull(task_ids="tarea0")

    print("Hola")
    print(xcom_value)

    return {"ok": 2}


tarea0 = PythonOperator(task_id="tarea0", python_callable=tarea0_func, dag=dag)

tarea1 = BashOperator(task_id="print_date", bash_command='echo "La fecha es $(date)"', dag=dag)

tarea2 = PythonOperator(task_id="tarea2", python_callable=tarea2_func, dag=dag)

# cuando termine tarea0, se ejecutan tarea1 y tarea2
tarea0 >> [tarea1, tarea2]
