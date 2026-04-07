import os
import boto3
from botocore.exceptions import ClientError
from src.application.service_ports.auth_service import IAuthService
from application.exceptions.auth_errors import (
    AuthError, UserAlreadyExistsError, InvalidCredentialsError,
    UserNotConfirmedError, CodeMismatchError, UserNotFoundError, ExpiredCodeError,
)

_ERROR_MAP = {
    "UsernameExistsException":    UserAlreadyExistsError,
    "NotAuthorizedException":     InvalidCredentialsError,
    "UserNotConfirmedException":  UserNotConfirmedError,
    "CodeMismatchException":      CodeMismatchError,
    "UserNotFoundException":      UserNotFoundError,
    "ExpiredCodeException":       ExpiredCodeError,
}


def _map_error(e: ClientError) -> AuthError:
    code = e.response["Error"]["Code"]
    msg  = e.response["Error"]["Message"]
    return _ERROR_MAP.get(code, AuthError)(msg)


class CognitoAdapter(IAuthService):
    def __init__(self, client=None):
        self._client = client or boto3.client("cognito-idp")
        self._client_id = os.environ["COGNITO_CLIENT_ID"]

    def _call(self, fn, **kwargs):
        try:
            return fn(ClientId=self._client_id, **kwargs)
        except ClientError as e:
            raise _map_error(e)

    def sign_up(self, email, password):
        self._call(
            self._client.sign_up,
            Username=email,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": email}],
        )

    def confirm_sign_up(self, email, code):
        self._call(self._client.confirm_sign_up, Username=email, ConfirmationCode=code)

    def sign_in(self, email, password) -> dict:
        result = self._call(
            self._client.initiate_auth,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": email, "PASSWORD": password},
        )
        tokens = result["AuthenticationResult"]
        return {
            "access_token": tokens["AccessToken"],
            "id_token":     tokens["IdToken"],
            "refresh_token": tokens["RefreshToken"],
        }

    def refresh_token(self, refresh_token) -> dict:
        result = self._call(
            self._client.initiate_auth,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": refresh_token},
        )
        tokens = result["AuthenticationResult"]
        return {"access_token": tokens["AccessToken"], "id_token": tokens["IdToken"]}

    def forgot_password(self, email):
        self._call(self._client.forgot_password, Username=email)

    def reset_password(self, email, code, new_password):
        self._call(
            self._client.confirm_forgot_password,
            Username=email,
            ConfirmationCode=code,
            Password=new_password,
        )

    def sign_out(self, access_token):
        try:
            self._client.global_sign_out(AccessToken=access_token)
        except ClientError as e:
            raise _map_error(e)
