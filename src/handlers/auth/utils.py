import json
import boto3
import os

cognito = boto3.client("cognito-idp")
CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
