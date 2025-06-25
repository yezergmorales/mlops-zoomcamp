# Different Ways to Send Data to Kinesis

## Method 1: Single line JSON (Recommended)
```bash
KINESIS_STREAM_INPUT=ride-events
aws kinesis put-record \
    --stream-name ${KINESIS_STREAM_INPUT} \
    --partition-key 1 \
    --data '{"ride": {"PULocationID": 130, "DOLocationID": 205, "trip_distance": 3.66}, "ride_id": 156}'
```

## Method 2: Using a file (Most reliable for complex JSON)
First create a JSON file:
```bash
echo '{"ride": {"PULocationID": 130, "DOLocationID": 205, "trip_distance": 3.66}, "ride_id": 156}' > test_data.json
```

Then send it:
```bash
KINESIS_STREAM_INPUT=ride-events
aws kinesis put-record \
    --stream-name ${KINESIS_STREAM_INPUT} \
    --partition-key 1 \
    --data file://test_data.json
```

## Method 3: Using environment variable
```bash
KINESIS_STREAM_INPUT=ride-events
TEST_DATA='{"ride": {"PULocationID": 130, "DOLocationID": 205, "trip_distance": 3.66}, "ride_id": 156}'
aws kinesis put-record \
    --stream-name ${KINESIS_STREAM_INPUT} \
    --partition-key 1 \
    --data "$TEST_DATA"
```

## Method 4: Base64 encoded (if you need to send binary data)
```bash
KINESIS_STREAM_INPUT=ride-events
# First encode your JSON as base64
DATA_B64=$(echo '{"ride": {"PULocationID": 130, "DOLocationID": 205, "trip_distance": 3.66}, "ride_id": 156}' | base64 -w 0)
aws kinesis put-record \
    --stream-name ${KINESIS_STREAM_INPUT} \
    --partition-key 1 \
    --data "$DATA_B64"
```

## Test with simple string first
```bash
KINESIS_STREAM_INPUT=ride-events
aws kinesis put-record \
    --stream-name ${KINESIS_STREAM_INPUT} \
    --partition-key 1 \
    --data "Hello, this is a test."
``` 