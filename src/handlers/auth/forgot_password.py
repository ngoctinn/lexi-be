import json
from botocore.exceptions import ClientError
from utils import cognito, CLIENT_ID, response


def handler(event, context):
    body = json.loads(event["body"])
    try:
        cognito.forgot_password(
            ClientId=CLIENT_ID,
            Username=body["email"],
        )
        return response(200, {"message": "Password reset code sent to email."})
    except ClientError as e:
        return response(400, {"error": e.response["Error"]["Message"]})
