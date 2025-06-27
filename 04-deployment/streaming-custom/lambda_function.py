import os
import json
import boto3
import base64
from typing import Dict, List, Any
import mlflow

kinesis_client = boto3.client('kinesis')

PREDICTIONS_STREAM_NAME = os.getenv('PREDICTIONS_STREAM_NAME', 'ride-predictions')
RUN_ID = os.getenv('RUN_ID', '008260e4b5964963ac9d0b969c887af2')

# Load model directly from S3 (better for Lambda)
logged_model = f's3://mlflow-models-alexey/1/{RUN_ID}/artifacts/model'
model = mlflow.pyfunc.load_model(logged_model)

TEST_RUN = os.getenv('TEST_RUN', 'False') == 'True'

def prepare_features(ride: Dict[str, Any]) -> Dict[str, Any]:
    features = {}
    features['PU_DO'] = '%s_%s' % (ride['PULocationID'], ride['DOLocationID'])
    features['trip_distance'] = ride['trip_distance']
    return features


def predict(features: Dict[str, Any]) -> float:
    pred = model.predict(features)
    return float(pred[0])


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, List[Dict[str, Any]]]:
    # print(json.dumps(event))
    
    predictions_events = []
    
    for record in event['Records']:
        encoded_data = record['kinesis']['data']
        
        # Handle the base64 decoding more robustly
        try:
            # First decode from base64
            decoded_bytes = base64.b64decode(encoded_data)
            # Try to decode as UTF-8
            decoded_data = decoded_bytes.decode('utf-8')
        except UnicodeDecodeError as e:
            # If UTF-8 decoding fails, try with different encodings
            print(f"UTF-8 decode error: {e}")
            try:
                # Try latin-1 encoding which can handle any byte sequence
                decoded_data = decoded_bytes.decode('latin-1')
                print("Successfully decoded using latin-1")
            except Exception as e2:
                # Last resort: ignore errors
                decoded_data = decoded_bytes.decode('utf-8', errors='ignore')
                print(f"Warning: Had to ignore some characters. Original error: {e}, Fallback error: {e2}")
        
        try:
            ride_event = json.loads(decoded_data)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Problematic data: {decoded_data}")
            continue  # Skip this record

        # print(ride_event)
        ride = ride_event['ride']
        ride_id = ride_event['ride_id']
    
        features = prepare_features(ride)
        prediction = predict(features)
    
        prediction_event = {
            'model': 'ride_duration_prediction_model',
            'version': '123',
            'prediction': {
                'ride_duration': prediction,
                'ride_id': ride_id   
            }
        }

        if not TEST_RUN:
            kinesis_client.put_record(
                StreamName=PREDICTIONS_STREAM_NAME,
                Data=json.dumps(prediction_event),
                PartitionKey=str(ride_id)
            )
        
        predictions_events.append(prediction_event)


    return {
        'predictions': predictions_events
    }
