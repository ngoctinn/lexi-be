from botocore.exceptions import ClientError
from utils import cognito, CLIENT_ID, response, parse_body, require_fields


def handler(event, context):
    try:
        body = parse_body(event)
        require_fields(body, "email")
    except ValueError as e:
        return response(400, {"error": str(e)})

    try:
        cognito.forgot_password(ClientId=CLIENT_ID, Username=body["email"])
        return response(200, {"message": "Password reset code sent to email."})
    except ClientError as e:
        return response(400, {"error": e.response["Error"]["Message"]})
