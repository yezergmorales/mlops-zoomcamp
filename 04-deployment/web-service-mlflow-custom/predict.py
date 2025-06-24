from typing import Any, Dict
import uvicorn

from fastapi import FastAPI
from pydantic import BaseModel
import mlflow
from mlflow.tracking import MlflowClient
import os

RUN_ID = os.getenv('RUN_ID', '008260e4b5964963ac9d0b969c887af2')  # Default value if not set via environment
print("RUN_ID", RUN_ID)

# Detect if running inside Docker by checking for common Docker environment indicators
def is_running_in_docker() -> bool:
    # Check for .dockerenv file (created by Docker)
    if os.path.exists('/.dockerenv'):
        return True
    # Check for Docker-specific environment variables
    if os.environ.get('DOCKER_CONTAINER', '').lower() == 'true':
        return True
    # Check if we're running as PID 1 (common in Docker containers)
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except (FileNotFoundError, PermissionError):
        pass
    return False

# Set MLflow tracking URI based on environment
if is_running_in_docker():
    MLFLOW_TRACKING_URI = "http://host.docker.internal:5000"  # inside the container
else:
    MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"  # in local
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Download the model artifact to local directory (e.g., ./model/)
client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
path = client.download_artifacts(run_id=RUN_ID, path='model')

# Load the model from the local path instead of the MLflow URI
loaded_model = mlflow.sklearn.load_model(path)


class Ride(BaseModel):
    PULocationID: str
    DOLocationID: str
    trip_distance: float


def prepare_features(ride: Ride) -> Dict[str, Any]:
    features: Dict[str, Any] = {}
    features['PU_DO'] = f'{ride.PULocationID}_{ride.DOLocationID}'
    features['trip_distance'] = ride.trip_distance
    return features


def predict(features: Dict[str, Any]) -> float:
    # The loaded_model is already in memory, so this function just uses it
    # No need to reload the model on each prediction call
    preds = loaded_model.predict(features)
    return float(preds[0])

app = FastAPI()


@app.post('/predict')
def predict_endpoint(ride: Ride) -> Dict[str, float]:
    features = prepare_features(ride)
    pred = predict(features)

    result = {
        'duration': pred,
    }

    return result


# To launch the server for testing, run one of these commands:
# 1. Using uvicorn directly from command line:
#    uvicorn predict:app --host 0.0.0.0 --port 9696
# 
# 2. Using python directly:
#    python predict.py
#    uv run predict.py
#    export RUN_ID=your_run_id && uv run predict.py
# 
# 3. Using uvicorn with reload for development:
#    uvicorn predict:app --host 0.0.0.0 --port 9696 --reload

# launch test.py to test the server
# 1. python test.py
# 2. curl -X POST http://localhost:9696/predict -H 'Content-Type: application/json' -d '{"PULocationID": "10", "DOLocationID": "50", "trip_distance": 10}'

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=9696)