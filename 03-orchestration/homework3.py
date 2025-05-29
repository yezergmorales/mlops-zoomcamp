import pandas as pd
import pickle
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import root_mean_squared_error
import xgboost as xgb
import mlflow
import os
import scipy.sparse
from typing import Union, Any
import numpy as np
import argparse

# To set or restart the tracking server: $ mlflow server --backend-store-uri sqlite:///backend.db

def create_models_folder(folder_name: str) -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, folder_name)

    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"Folder '{models_dir}' created.")

    return models_dir


def read_dataframe(color_line: str, year: int, month: int) -> pd.DataFrame:
    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{color_line}_tripdata_{year:4}-{month:02}.parquet"
    df = pd.read_parquet(url)
    print(f"raw records-{year}-{month}: df.shape: {df.shape}")

    if color_line == "yellow":
        df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
        df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
        df["duration"] = df.tpep_dropoff_datetime - df.tpep_pickup_datetime
    else:
        df.lpep_dropoff_datetime = pd.to_datetime(df.lpep_dropoff_datetime)
        df.lpep_pickup_datetime = pd.to_datetime(df.lpep_pickup_datetime)
        df["duration"] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime

    df.duration = df.duration.apply(lambda td: td.total_seconds() / 60)

    df = df[(df.duration >= 1) & (df.duration <= 60)]

    categorical = ["PULocationID", "DOLocationID"]
    df[categorical] = df[categorical].astype(str)

    df["PU_DO"] = df["PULocationID"] + "_" + df["DOLocationID"]

    return df


def create_X(
    df: pd.DataFrame, dv: Union[DictVectorizer, None] = None
) -> tuple[scipy.sparse.csr_matrix, DictVectorizer]:
    categorical = ["PU_DO"]
    numerical = ["trip_distance"]
    dicts = df[categorical + numerical].to_dict(orient="records")

    if dv is None:
        # The `sparse=True` argument specifies that the output of the transformation
        # should be a SciPy sparse matrix rather than a dense NumPy array.
        dv = DictVectorizer(sparse=True)
        X = dv.fit_transform(dicts)
    else:
        X = dv.transform(dicts)

    return X, dv


def train_model(
    X_train: scipy.sparse.csr_matrix,
    y_train: np.ndarray[Any, Any],
    X_val: scipy.sparse.csr_matrix,
    y_val: np.ndarray[Any, Any],
    dv: DictVectorizer,
    models_dir: str,
) -> str:
    train = xgb.DMatrix(X_train, label=y_train)
    valid = xgb.DMatrix(X_val, label=y_val)

    with mlflow.start_run():
        best_params = {
            "learning_rate": 0.09585355369315604,
            "max_depth": 30,
            "min_child_weight": 1.060597050922164,
            "objective": "reg:squarederror",
            "reg_alpha": 0.018060244040060163,
            "reg_lambda": 0.011658731377413597,
            "seed": 42,
        }

        mlflow.log_params(best_params)

        # Using 'valid' in 'evals' is good practice for XGBoost training.
        # It enables early stopping, which monitors performance on the validation set
        # during training and stops when performance no longer improves.
        # While this means the validation set's information guides the training duration (number of rounds),
        # this is its intended purpose to prevent overfitting to the training data.
        # A separate, final test set should still be used for unbiased evaluation of the trained model.
        booster = xgb.train(
            params=best_params,
            dtrain=train,
            num_boost_round=1,
            evals=[(valid, "validation")],
            early_stopping_rounds=50,
        )

        y_pred = booster.predict(valid)
        rmse = root_mean_squared_error(y_val, y_pred)
        mlflow.log_metric("rmse", rmse)

        with open(f"{models_dir}/preprocessor.b", "wb") as f_out:
            pickle.dump(dv, f_out)
        mlflow.log_artifact(f"{models_dir}/preprocessor.b", artifact_path="preprocessor")

        mlflow.xgboost.log_model(booster, artifact_path="models_mlflow")

        # Get the active run ID and return it
        active_run = mlflow.active_run()
        if active_run:
            return str(active_run.info.run_id)
        else:
            # This case should ideally not be reached if inside `with mlflow.start_run():`
            # Depending on desired behavior, could raise an error or return None.
            # For this exercise, we assume an active run exists.
            # If strictly following "return run_id", and no run_id exists, an error might be appropriate.
            # However, to avoid breaking existing None return type if run fails, returning None might be safer
            # but doesn't fulfill "return run_id".
            # Given the context, active_run should exist.
            raise RuntimeError("MLflow active run not found, cannot return run_id.")


def run(color_line: str, year: int, month: int, tracking_uri: str, experiment_name: str) -> None:
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    models_folder = "models"
    models_dir = create_models_folder(models_folder)

    train_year = year
    train_month = month
    if train_month == 12:
        val_year = year + 1
        val_month = 1
    else:
        val_year = year
        val_month = month + 1

    df_train = read_dataframe(color_line=color_line, year=train_year, month=train_month)
    df_val = read_dataframe(color_line=color_line, year=val_year, month=val_month)
    print(f"df_train.shape: {df_train.shape} --> year: {train_year}, month: {train_month}")
    print(f"df_val.shape: {df_val.shape} --> year: {val_year}, month: {val_month}")

    X_train, dv = create_X(df_train)
    X_val, _ = create_X(df_val, dv)

    target = "duration"
    run_id = train_model(X_train, df_train[target].values, X_val, df_val[target].values, dv, models_dir)
    print(f"run_id: {run_id}")

    # Save the run_id to a local text file. Needed to promote the model with orchestrators
    script_dir = os.path.dirname(os.path.abspath(__file__))
    run_id_file = os.path.join(script_dir, "run_id.txt")
    with open(run_id_file, "w") as f:
        f.write(run_id)
    print(f"Saved run_id to {run_id_file}")

    # Registering the model with MLFlow
    client = mlflow.MlflowClient(tracking_uri=tracking_uri)
    experiment = client.get_experiment_by_name(experiment_name)
    if not experiment:
        raise ValueError(f"Experiment '{experiment_name}' not found.")
    model_uri = f"runs:/{run_id}/models_mlflow"
    mlflow.register_model(
        model_uri=model_uri,
        name=experiment_name,
    )
    versions = client.search_model_versions(filter_string=f"name='{experiment_name}'")
    for version in versions:
        if version.run_id == run_id:
            loaded_model = mlflow.pyfunc.load_model(model_uri=model_uri)
            print(f"---------------------> Model size: {loaded_model._model_meta.model_size_bytes}")
            break
    else:
        raise ValueError(f"Model with run_id '{run_id}' not found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a model on a given year and month")
    parser.add_argument("-cl", "--color_line", type=str, help="Color line for the NYC taxi data")
    parser.add_argument("-y", "--year", type=int, help="Year for the training data")
    parser.add_argument("-m", "--month", type=int, help="Month for the training data")
    parser.add_argument(
        "-tu", "--tracking_uri",
        type=str,
        default="http://127.0.0.1:5000",
        help="MLflow tracking URI",
        required=False,
    )
    parser.add_argument(
        "-en", "--experiment_name",
        type=str,
        default="nyc-taxi-experiment",
        help="MLflow experiment name",
        required=False,
    )
    args = parser.parse_args()
    year = args.year
    month = args.month
    color_line = args.color_line
    tracking_uri = args.tracking_uri
    experiment_name = args.experiment_name
    run(
        color_line=color_line,
        year=year, month=month,
        tracking_uri=tracking_uri,
        experiment_name=experiment_name)
