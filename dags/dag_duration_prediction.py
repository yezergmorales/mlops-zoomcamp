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
        "TRACKER_SCRIPT_PATH": "/home/yezer/projects/mlops-zoomcamp/03-orchestration/homework3_set_tracker.py",
        "MODEL_FOLDER_SCRIPT_PATH": "/home/yezer/projects/mlops-zoomcamp/03-orchestration/homework3_create_model_folder.py",
        "LOAD_DATA_SCRIPT_PATH": "/home/yezer/projects/mlops-zoomcamp/03-orchestration/homework3_load_data.py",
        "TRANSFORM_DATA_SCRIPT_PATH": "/home/yezer/projects/mlops-zoomcamp/03-orchestration/homework3_transform_data.py",
        "TRAIN_MODEL_SCRIPT_PATH": "/home/yezer/projects/mlops-zoomcamp/03-orchestration/homework3_train_model.py",
        "FIND_LOAD_LOGGED_MODEL_SCRIPT_PATH": "/home/yezer/projects/mlops-zoomcamp/03-orchestration/homework3_find_load_logged_model.py",
        "MODEL_FOLDER": "models",
        "VENV_PATH": "/home/yezer/projects/mlops-zoomcamp",
        "COLOR_LINE": "yellow",
        "YEAR": 2023,
        "MONTH": 3,
    },
)


def task0_func(**kwargs: Any) -> Dict[str, str]:
    print("Welcome cripto-bro!")
    return {"task0": "ok"}


task0 = PythonOperator(
    task_id="hello-task",
    python_callable=task0_func,
    retries=2,
    dag=dag,
)

task1 = BashOperator(
    task_id="create-model-folder-task",
    bash_command="""
        source {{params.VENV_PATH}}/.venv/bin/activate
        python {{params.MODEL_FOLDER_SCRIPT_PATH}} --model_folder {{params.MODEL_FOLDER}}
    """,
    dag=dag,
)

task2 = BashOperator(
    task_id="load-data-task",
    bash_command="""
        source {{params.VENV_PATH}}/.venv/bin/activate
        python {{params.LOAD_DATA_SCRIPT_PATH}} --color_line {{params.COLOR_LINE}} --year {{params.YEAR}} --month {{params.MONTH}}
    """,
    dag=dag,
)

task3 = BashOperator(
    task_id="transform-data-task",
    bash_command="""
        source {{params.VENV_PATH}}/.venv/bin/activate
        XCOM_OUTPUT_PATHS=$(echo '{{ ti.xcom_pull(task_ids="load-data-task") }}')
        DF_TRAIN_PATH=$(echo $XCOM_OUTPUT_PATHS | python -c "import sys, json; print(json.load(sys.stdin)['df_train_path'])")
        DF_VAL_PATH=$(echo $XCOM_OUTPUT_PATHS | python -c "import sys, json; print(json.load(sys.stdin)['df_val_path'])")
        XCOM_OUTPUT_MODEL_FOLDER=$(echo '{{ ti.xcom_pull(task_ids="create-model-folder-task") }}')
        MODELS_DIR=$(echo $XCOM_OUTPUT_MODEL_FOLDER | python -c "import sys, json; print(json.load(sys.stdin)['models_dir'])")
        python {{params.TRANSFORM_DATA_SCRIPT_PATH}} \
            --df_train_path $DF_TRAIN_PATH \
            --df_val_path $DF_VAL_PATH \
            --models_dir $MODELS_DIR
    """,
    dag=dag,
)

task4 = BashOperator(
    task_id="train-model-task",
    bash_command="""
        source {{params.VENV_PATH}}/.venv/bin/activate
        XCOM_OUTPUT_PATHS=$(echo '{{ ti.xcom_pull(task_ids="transform-data-task") }}')
        X_TRAIN_PATH=$(echo $XCOM_OUTPUT_PATHS | python -c "import sys, json; print(json.load(sys.stdin)['x_train_path'])")
        Y_TRAIN_PATH=$(echo $XCOM_OUTPUT_PATHS | python -c "import sys, json; print(json.load(sys.stdin)['y_train_path'])")
        X_VAL_PATH=$(echo $XCOM_OUTPUT_PATHS | python -c "import sys, json; print(json.load(sys.stdin)['x_val_path'])")
        Y_VAL_PATH=$(echo $XCOM_OUTPUT_PATHS | python -c "import sys, json; print(json.load(sys.stdin)['y_val_path'])")
        DV_PATH=$(echo $XCOM_OUTPUT_PATHS | python -c "import sys, json; print(json.load(sys.stdin)['dv_path'])")
        python {{params.TRAIN_MODEL_SCRIPT_PATH}} --x_train_out_path $X_TRAIN_PATH \
            --y_train_out_path $Y_TRAIN_PATH \
            --x_val_out_path $X_VAL_PATH \
            --y_val_out_path $Y_VAL_PATH \
            --dv_path $DV_PATH 
    """,
    dag=dag,
)

task5 = BashOperator(
    task_id="find-load-logged-model-task",
    bash_command="""
        source {{params.VENV_PATH}}/.venv/bin/activate
        python {{params.FIND_LOAD_LOGGED_MODEL_SCRIPT_PATH}}
    """,
    dag=dag,
)


task0 >> task1 >> task2 >> task3 >> task4 >> task5
