Lambda with Kinesis Data Streams lets you process streaming data in real time, with automatic scaling and minimal setup. You write code to process data, and AWS handles the rest—polling, batching, retries, and checkpointing

![image.png](image.png)

https://docs.amazonaws.cn/en_us/lambda/latest/dg/with-kinesis-example.html

kinesis test:
{
    "Records": [
        {
            "kinesis": {
                "kinesisSchemaVersion": "1.0",
                "partitionKey": "1",
                "sequenceNumber": "49664606472349696372092827741651184142175384785261690882",
                "data": "eyJyaWRlIjogeyJQVUxvY2F0aW9uSUQiOiAxMzAwMCwgIkRPTG9jYXRpb25JRCI6IDIwNSwgInRyaXBfZGlzdGFuY2UiOiAzLjY2fSwgInJpZGVfaWQiOiAxNTZ9Cg==",
                "approximateArrivalTimestamp": 1750925642.262
            },
            "eventSource": "aws:kinesis",
            "eventVersion": "1.0",
            "eventID": "shardId-000000000000:49664606472349696372092827741651184142175384785261690882",
            "eventName": "aws:kinesis:record",
            "invokeIdentityArn": "arn:aws:iam::125106255178:role/lambda-kinesis-role",
            "awsRegion": "eu-west-2",
            "eventSourceARN": "arn:aws:kinesis:eu-west-2:125106255178:stream/ride-events"
        }
    ]
}

1. Create a role for the lambda function
   - 1.1 Look for Access managemet in IAM / roles
   - 1.2 create a role for the lambda function
   - 1.3 we add permission: AWSLambdaKinesisExecutionRole
   - 1.4 set role name: lambda-kinesis-role

2. Create a lambda function.
    - 2.1 set a name
    - 2.2 set the runtime: 3.12 (the version I have used in this project)
    - 2.3 Architecture: x86_64
    - 2.4 Change the default execution role to the one we created in the previous step
    - 2.5 we can write the code of the lambda function in the code editor.
    - 2.6 deploy the function.
    - 2.7 create a new test event.

3. Connect with Kinesis.
    - 3.1 creamos a kinesis data stream.
        - Para la prueba, provisioned, y 1 shard en este caso.
        "Each shard ingests up to 1 MiB/second and 1,000 records/second and emits up to 2 MiB/second. If writes and reads exceed capacity, the application will receive throttles."
        **Es importante borrar el stream cuando ya no se necesite ya que cada hora representa gastos**
    - 3.2 En function overview, podemos añadir un trigger. Ahí es donde conectamos con Kinesis.
        - 3.2.1 En el trigger, seleccionamos el stream que hemos creado.
    - 3.3 Para probar lo que hemos hecho, necesitamos enviar un evento de test al stream, y deberíamos ver a lambda reaccionando al test event.

    *we run in (base) where we have installed aws cli*
    *in our case, partition-key will be ride_id, is the way to identify a request*
    *We need to configure a region, in our case eu-west-2. We can do in running aws configure*
    *después de lanzar el comando podemos ver los logs en CloudWatch de Lambda"

    ```bash
    aws kinesis put-record \
        --stream-name ride-events-reading \
        --partition-key 1 \
        --data "$(echo -n '{"ride": {"PULocationID": 10, "DOLocationID": 50, "trip_distance": 40.66}, "ride_id": 459}' | base64)"
    ```
4. We add a new kinesis data stream to read data from the function. The function actually writes to the stream we are going to create (ride-predictions)
    4.0 We create a kinesis ride-predictions
    4.1 We need add the policy to the lambda-kinesis-role.
    In policies (IAM) create a new policy to attach to kinesis data stream role.
        4.1.1 Kinesis service, put record & put records.
        4.1.2 we add the arn, what is the especific resource we use.
        arn:aws:kinesis:eu-west-2:125106255178:stream/ride-predictions we can see if we test the lambda function.
        Policy name: lambda_kinesis_write_to_ride_predictions
        4.1.3: finally we attach the policy to the rol lambda-kinesis-role
    4.3 We execute the kinesis test event.

    ### Reading from the stream after the test of send an event to lambda function
    An event is sent, is detected by kinesis, that executes the lambda function and then writes the lambda function to another kinesis stream.

    *this gives us the first record in the stream*
    ```bash
    SHARD='shardId-000000000000'
    SHARD_ITERATOR=$(aws kinesis \
        get-shard-iterator \
            --shard-id ${SHARD} \
            --shard-iterator-type TRIM_HORIZON \
            --stream-name ride-predictions \
            --query 'ShardIterator' \
    )
    RESULT=$(aws kinesis get-records --shard-iterator $SHARD_ITERATOR)
    echo ${RESULT} | jq -r '.Records[0].Data' | base64 --decode
    ``` 

    *This gives you a pointer to the end of the stream. But it will return nothing unless a new record is added after this step*
    ```bash
        SHARD_ITERATOR=$(aws kinesis get-shard-iterator \
        --stream-name ride-predictions \
        --shard-id shardId-000000000000 \
        --shard-iterator-type LATEST \
        --query 'ShardIterator' \
        --output text)
    ```

    ```bash
    aws kinesis put-record \
        --stream-name ride-events-reading \
        --partition-key 1 \
        --data "$(echo -n '{"ride": {"PULocationID": 130, "DOLocationID": 205, "trip_distance": 3.66}, "ride_id": 111}' | base64)"
    ```

    *Fetch new records:
    ```bash
    aws kinesis get-records \
    --shard-iterator $SHARD_ITERATOR \
    --output json

5. Launch the mlflow tracking server.
    ```bash
    mlflow server --backend-store-uri sqlite:///backend.db --default-artifact-root=s3://yezer-artifacts-remote-01
    ```
6. We take the lambda function to lambda_function.py inside my project, but with some modifications to read the model from the mlflow tracking server.

7. We check the lambda_function.py
    ```bash
    uv run test.py
    ```

8. Create the Docker image.
    ```bash
    docker build -t stream-model-duration:v1 .
    ```

9. Run the docker image
    ```bash	
    docker run -it --rm \
        -p 8080:8080 \
        -v ~/.aws:/root/.aws:ro \
        -e PREDICTIONS_STREAM_NAME="ride-predictions" \
        -e RUN_ID="008260e4b5964963ac9d0b969c887af2" \
        -e TEST_RUN="True" \
        -e AWS_DEFAULT_REGION="eu-west-2" \
        stream-model-duration:v1
    ```
    *After this we only need events in the stream ride-events-reading to be processed by the lambda function.*

10. Test the docker image.
    ```bash	
    uv run test_docker.py
    ```

11. Publishing Docker images

    Creating an ECR repo

    ```bash
    aws ecr create-repository --repository-name duration-model
    ```

    Logging in

    ```bash
    aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 125106255178.dkr.ecr.eu-west-2.amazonaws.com
    ```

    Pushing 

    ```bash
    REMOTE_URI="125106255178.dkr.ecr.eu-west-2.amazonaws.com/duration-model"
    REMOTE_TAG="v1"
    REMOTE_IMAGE=${REMOTE_URI}:${REMOTE_TAG}

    LOCAL_IMAGE="stream-model-duration:v1"
    docker tag ${LOCAL_IMAGE} ${REMOTE_IMAGE}
    docker push ${REMOTE_IMAGE}
```

12. Use the pushed image in Lambda
    12.1
    ```bash
    echo $REMOTE_IMAGE
    ```
    En este caso -- > 125106255178.dkr.ecr.eu-west-2.amazonaws.com/duration-model:v1
    ```
    
    12.2 Create a Lambda function to use the pushed image. We select 'lambda-kinesis-role' in permissions.

    12.3 Configure variables.
    Once the function is created we go to 'configuration' in Lambda in AWS, in our function.
    - Environment variables:
        - PREDICTIONS_STREAM_NAME: ride-predictions
        - RUN_ID: 008260e4b5964963ac9d0b969c887af2
    
    12.4 We add a trigger to the function.
        - Kinesis/ride-events-reading

13. Check if it works.
    ```bash	
        aws kinesis put-record \
        --stream-name ride-events-reading \
        --partition-key 1 \
        --data "$(echo -n '{"ride": {"PULocationID": 30, "DOLocationID": 95, "trip_distance": 32.888}, "ride_id": 100}' | base64)"
    ```
    It is not working how you can see. We have to give permission to lambda to access to S3.
    Create a policy to access to S3. 
        - Mark List and Read permissions when are creating the policy.
        - Resources. Bucket. Add ARN. Just for the bucket name
        - Objects. Put the bucket name again and in object name * (any object name)
    We add the permission to the role lambda-kinesis-role.

    Still fails, we gives more time, in function configuration
    












    









