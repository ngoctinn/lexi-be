import json
from botocore.exceptions import ClientError
from utils import cognito, CLIENT_ID, response


def handler(event, context):
    body = json.loads(event["body"])
    try:
        cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=body["email"],
            Password=body["password"],
            UserAttributes=[{"Name": "email", "Value": body["email"]}],
        )
        return response(201, {"message": "User created. Check email for confirmation code."})
    except ClientError as e:
        return response(400, {"error": e.response["Error"]["Message"]})
