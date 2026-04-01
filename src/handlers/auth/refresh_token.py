import json
from botocore.exceptions import ClientError
from utils import cognito, CLIENT_ID, response


def handler(event, context):
    body = json.loads(event["body"])
    try:
        result = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": body["refresh_token"]},
        )
        tokens = result["AuthenticationResult"]
        return response(200, {
            "access_token": tokens["AccessToken"],
            "id_token": tokens["IdToken"],
        })
    except ClientError as e:
        return response(401, {"error": e.response["Error"]["Message"]})
