## Deploying a model as a web-service

* Creating a script for predictiong 
* Putting the script into a FastAPI app
* Packaging the app to Docker

## Run the tracking server. In this case local, and artifacts in S3
```bash
`mlflow server --backend-store-uri sqlite:///backend.db --default-artifact-root=s3://yezer-artifacts-remote-01`
```

## Requirements from pyproject.toml
```bash
uv pip compile pyproject.toml -o requirements.txt
```

## Build the Docker image
```bash
docker build -t ride-duration-prediction-service:v1 .
```

## Remove the docker image
```bash
docker rmi ride-duration-prediction-service:v1 --force
```

## Remove the docker image by id
```bash
docker rmi <image_id> --force
```

## Check the docker image by cli
```bash
# This command lists all Docker images and filters to show only the ride-duration-prediction-service image
docker images | grep ride-duration-prediction-service
```

## Run the Docker container
```bash
# This command runs the Docker container with the following options:
# -it: Interactive mode with pseudo-TTY (allows you to see logs and interact with the container)
# --rm: Automatically remove the container when it stops (cleanup)
# -p 9696:9696: Port mapping - maps host port 9696 to container port 9696
#               This allows external access to the service running inside the container
# ride-duration-prediction-service:v1: The Docker image name and tag to run.
# now we have to pass aws credentials to connect to s3 bucket with artifacts.
docker run -it --rm -p 9696:9696 -v ~/.aws:/root/.aws:ro -e RUN_ID="c06055301c0b4bec9f7fff83866d7f21" ride-duration-prediction-service:v1
```

## Test the server
```bash
curl -X POST http://localhost:9696/predict -H 'Content-Type: application/json' -d '{"PULocationID": "10", "DOLocationID": "50", "trip_distance": 10}'
```


