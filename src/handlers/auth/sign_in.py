from botocore.exceptions import ClientError
from utils import cognito, CLIENT_ID, response, parse_body, require_fields


def handler(event, context):
    try:
        body = parse_body(event)
        require_fields(body, "email", "password")
    except ValueError as e:
        return response(400, {"error": str(e)})

    try:
        result = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": body["email"], "PASSWORD": body["password"]},
        )
        tokens = result["AuthenticationResult"]
        return response(200, {
            "access_token": tokens["AccessToken"],
            "id_token": tokens["IdToken"],
            "refresh_token": tokens["RefreshToken"],
        })
    except ClientError as e:
        return response(401, {"error": e.response["Error"]["Message"]})
