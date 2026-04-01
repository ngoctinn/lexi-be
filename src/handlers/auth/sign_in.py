import json
from botocore.exceptions import ClientError
from utils import cognito, CLIENT_ID, response


def handler(event, context):
    body = json.loads(event["body"])
    try:
        result = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": body["email"],
                "PASSWORD": body["password"],
            },
        )
        tokens = result["AuthenticationResult"]
        return response(200, {
            "access_token": tokens["AccessToken"],
            "id_token": tokens["IdToken"],
            "refresh_token": tokens["RefreshToken"],
        })
    except ClientError as e:
        return response(401, {"error": e.response["Error"]["Message"]})
