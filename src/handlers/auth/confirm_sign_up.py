from botocore.exceptions import ClientError
from utils import cognito, CLIENT_ID, response, parse_body, require_fields


def handler(event, context):
    try:
        body = parse_body(event)
        require_fields(body, "email", "code")
    except ValueError as e:
        return response(400, {"error": str(e)})

    try:
        cognito.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=body["email"],
            ConfirmationCode=body["code"],
        )
        return response(200, {"message": "Account confirmed."})
    except ClientError as e:
        return response(400, {"error": e.response["Error"]["Message"]})
