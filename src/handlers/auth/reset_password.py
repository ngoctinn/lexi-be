import json
from botocore.exceptions import ClientError
from utils import cognito, CLIENT_ID, response


def handler(event, context):
    body = json.loads(event["body"])
    try:
        cognito.confirm_forgot_password(
            ClientId=CLIENT_ID,
            Username=body["email"],
            ConfirmationCode=body["code"],
            Password=body["new_password"],
        )
        return response(200, {"message": "Password reset successful."})
    except ClientError as e:
        return response(400, {"error": e.response["Error"]["Message"]})
