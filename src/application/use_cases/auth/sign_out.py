from src.application.ports.cognito_port import ICognitoPort
from src.application.dtos.auth_dto import SignOutDTO
from src.application.exceptions import AuthError


class SignOutUseCase:
    def __init__(self, port: ICognitoPort):
        self.port = port

    def execute(self, dto: SignOutDTO):
        if not dto.access_token:
            raise AuthError("Access token is required")
        self.port.sign_out(dto.access_token)

