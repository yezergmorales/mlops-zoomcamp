from sklearn.metrics import root_mean_squared_error
import mlflow
import os
import scipy.sparse
import numpy as np
import argparse
import shutil
from sklearn.linear_model import LinearRegression


def train_model(
    x_train_out_path: str,
    y_train_out_path: str,
    x_val_out_path: str,
    y_val_out_path: str,
    dv_path: str,
    tracking_uri: str,
    experiment_name: str,
) -> str:
    
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    
    X_train = scipy.sparse.load_npz(x_train_out_path)
    y_train = np.load(y_train_out_path)
    X_val = scipy.sparse.load_npz(x_val_out_path)
    y_val = np.load(y_val_out_path)

    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    shutil.rmtree(temp_dir)

    mlflow.autolog(disable=True)
    with mlflow.start_run():
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        
        rmse = root_mean_squared_error(y_val, y_pred)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_artifact(dv_path, artifact_path='preprocessor')
        mlflow.sklearn.log_model(model, artifact_path='models_mlflow')
        print(f"------------------------> Intercept: {model.intercept_}")

        del X_train, y_train, X_val, y_val, y_pred, rmse

        # Get the active run ID and return it
        active_run = mlflow.active_run()
        if active_run:
            return str(active_run.info.run_id)
        else:
            raise RuntimeError("MLflow active run not found, cannot return run_id.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a model")
    parser.add_argument("--x_train_out_path", type=str, help="path to X_train")
    parser.add_argument("--y_train_out_path", type=str, help="path to y_train")
    parser.add_argument("--x_val_out_path", type=str, help="path to X_val")
    parser.add_argument("--y_val_out_path", type=str, help="path to y_val")
    parser.add_argument("--dv_path", type=str, help="path to dv")
    parser.add_argument("--tracking_uri", type=str, default="http://127.0.0.1:5000", help="MLflow tracking URI")
    parser.add_argument("--experiment_name", type=str, default="nyc-taxi-experiment", help="MLflow experiment name")
    args = parser.parse_args()
    x_train_out_path = args.x_train_out_path
    y_train_out_path = args.y_train_out_path
    x_val_out_path = args.x_val_out_path
    y_val_out_path = args.y_val_out_path
    tracking_uri = args.tracking_uri
    experiment_name = args.experiment_name
    dv_path = args.dv_path

    run_id = train_model(
        x_train_out_path=x_train_out_path,
        y_train_out_path=y_train_out_path,
        x_val_out_path=x_val_out_path,
        y_val_out_path=y_val_out_path,
        dv_path=dv_path,
        tracking_uri=tracking_uri,
        experiment_name=experiment_name
    )
    print(f"run_id: {run_id}")

    # Save the run_id to a local text file. Needed to promote the model with orchestrators
    script_dir = os.path.dirname(os.path.abspath(__file__))
    run_id_file = os.path.join(script_dir, "run_id.txt")
    with open(run_id_file, "w") as f:
        f.write(run_id)
    print(f"Saved run_id to {run_id_file}")


