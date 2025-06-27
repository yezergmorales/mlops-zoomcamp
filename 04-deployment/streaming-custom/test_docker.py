import requests 

event = {
    "Records": [
        {
            "kinesis": {
                "kinesisSchemaVersion": "1.0",
                "partitionKey": "1",
                "sequenceNumber": "49630081666084879290581185630324770398608704880802529282",
                "data": "eyJyaWRlIjogeyJQVUxvY2F0aW9uSUQiOiAxMCwgIkRPTG9jYXRpb25JRCI6IDUwLCAidHJpcF9kaXN0YW5jZSI6IDQwLjY2fSwgInJpZGVfaWQiOiA0NTl9",
                "approximateArrivalTimestamp": 1654161514.132
            },
            "eventSource": "aws:kinesis",
            "eventVersion": "1.0",
            "eventID": "shardId-000000000000:49630081666084879290581185630324770398608704880802529282",
            "eventName": "aws:kinesis:record",
            "invokeIdentityArn": "arn:aws:iam::387546586013:role/lambda-kinesis-role",
            "awsRegion": "eu-west-2",
            "eventSourceARN": "arn:aws:kinesis:eu-west-2:125106255178:stream/ride-events-reading"
        }
    ]
}

"""The URL http://localhost:8080/2015-03-31/functions/function/invocations is the AWS Lambda Runtime Interface Emulator (RIE) endpoint. Let me explain where this comes from:
The URL is defined by the AWS Lambda base image public.ecr.aws/lambda/python:3.12. Here's how it works:
Where it's defined:
AWS Lambda Base Image: The FROM public.ecr.aws/lambda/python:3.12 contains the Lambda Runtime Interface Emulator (RIE)
Port 8080: The Lambda base image exposes port 8080 by default
Endpoint Path: /2015-03-31/functions/function/invocations is the standard AWS Lambda Runtime API endpoint"""

url = 'http://localhost:8080/2015-03-31/functions/function/invocations'
response = requests.post(url, json=event)
print(response.json())
