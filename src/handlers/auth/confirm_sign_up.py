import json
from botocore.exceptions import ClientError
from utils import cognito, CLIENT_ID, response


def handler(event, context):
    body = json.loads(event["body"])
    try:
        cognito.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=body["email"],
            ConfirmationCode=body["code"],
        )
        return response(200, {"message": "Account confirmed."})
    except ClientError as e:
        return response(400, {"error": e.response["Error"]["Message"]})
