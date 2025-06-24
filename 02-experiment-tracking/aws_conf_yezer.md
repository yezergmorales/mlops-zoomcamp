MLFlow setup
- tracking server: local (this is different from the the course config. where tracking server is a EC2 instance)
- artifact store: s3
- database: sqlite

1. AWS account. Sign-in to AWS account as root user.
    1.1 zone eu-west-2 (be sure always we are in this zone)

2. Create a new S3 bucket.

3. In cli to launch the server: `mlflow server --backend-store-uri sqlite:///backend.db --default-artifact-root=s3://yezer-artifacts-remote-01`

**Take a look at /home/yezer/projects/mlops-zoomcamp/02-experiment-tracking/running-mlflow-examples/scenario-4-custom.ipynb for more details.**

