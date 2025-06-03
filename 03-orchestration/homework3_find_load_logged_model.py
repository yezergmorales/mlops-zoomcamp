import mlflow
import os
import argparse

def find_and_load_logged_model(tracking_uri: str, experiment_name: str) -> None:

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    run_id_file = os.path.join(script_dir, "run_id.txt")
    with open(run_id_file, "r") as f:
        run_id = f.read()
    print(f"---------------------> run_id: {run_id}")

    # Loading the model from MLFlow using run_id
    model_uri = f"runs:/{run_id}/models_mlflow"
    try:
        print(f"Attempting to load model from URI: {model_uri}")
        loaded_model = mlflow.pyfunc.load_model(model_uri=model_uri)
        print(f"Successfully loaded model from run_id: {run_id}")

        if (
            hasattr(loaded_model, "_model_meta")
            and hasattr(loaded_model._model_meta, "model_size_bytes")
            and loaded_model._model_meta.model_size_bytes is not None
        ):
            print(f"---------------------> Model size: {loaded_model._model_meta.model_size_bytes} bytes")
        else:
            print(
                "---------------------> Model size information via _model_meta.model_size_bytes not available or is None."
            )

    except mlflow.exceptions.MlflowException as e:
        raise ValueError(f"Failed to load model with run_id '{run_id}' from URI '{model_uri}'. MLflow error: {e}")
    except Exception as e:
        raise ValueError(f"An unexpected error occurred while loading model with run_id '{run_id}'. Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load the logged model by run_id")
    parser.add_argument("--tracking_uri", type=str, default="http://127.0.0.1:5000", help="MLflow tracking URI")
    parser.add_argument("--experiment_name", type=str, default="nyc-taxi-experiment", help="MLflow experiment name")
    args = parser.parse_args()
    tracking_uri = args.tracking_uri
    experiment_name = args.experiment_name

    find_and_load_logged_model(tracking_uri=tracking_uri, experiment_name=experiment_name)
