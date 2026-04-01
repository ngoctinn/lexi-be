from botocore.exceptions import ClientError
from utils import cognito, response, parse_body, require_fields


def handler(event, context):
    try:
        body = parse_body(event)
        require_fields(body, "access_token")
    except ValueError as e:
        return response(400, {"error": str(e)})

    try:
        cognito.global_sign_out(AccessToken=body["access_token"])
        return response(200, {"message": "Signed out successfully."})
    except ClientError as e:
        return response(401, {"error": e.response["Error"]["Message"]})
