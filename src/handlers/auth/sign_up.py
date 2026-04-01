from botocore.exceptions import ClientError
from utils import cognito, CLIENT_ID, response, parse_body, require_fields


def handler(event, context):
    try:
        body = parse_body(event)
        require_fields(body, "email", "password")
    except ValueError as e:
        return response(400, {"error": str(e)})

    try:
        cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=body["email"],
            Password=body["password"],
            UserAttributes=[{"Name": "email", "Value": body["email"]}],
        )
        return response(201, {"message": "User created. Check email for confirmation code."})
    except ClientError as e:
        return response(400, {"error": e.response["Error"]["Message"]})
