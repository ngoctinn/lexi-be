from botocore.exceptions import ClientError
from utils import cognito, CLIENT_ID, response, parse_body, require_fields


def handler(event, context):
    try:
        body = parse_body(event)
        require_fields(body, "email", "code", "new_password")
    except ValueError as e:
        return response(400, {"error": str(e)})

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
