import pickle
from typing import Any, Dict
import uvicorn

from fastapi import FastAPI
from pydantic import BaseModel


class Ride(BaseModel):  # type: ignore
    PULocationID: str
    DOLocationID: str
    trip_distance: float


with open('lin_reg.bin', 'rb') as f_in:
    (dv, model) = pickle.load(f_in)


def prepare_features(ride: Ride) -> Dict[str, Any]:
    features: Dict[str, Any] = {}
    features['PU_DO'] = f'{ride.PULocationID}_{ride.DOLocationID}'
    features['trip_distance'] = ride.trip_distance
    return features


def predict(features: Dict[str, Any]) -> float:
    X = dv.transform(features)
    preds = model.predict(X)
    return float(preds[0])


app = FastAPI()


@app.post('/predict')  # type: ignore
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
# 
# 3. Using uvicorn with reload for development:
#    uvicorn predict:app --host 0.0.0.0 --port 9696 --reload

# launch test.py to test the server
# 1. python test.py
# 2. curl -X POST http://localhost:9696/predict -H 'Content-Type: application/json' -d '{"PULocationID": "10", "DOLocationID": "50", "trip_distance": 10}'

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=9696)