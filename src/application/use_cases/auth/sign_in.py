from src.application.ports.cognito_port import ICognitoPort
from src.application.dtos.auth_dto import SignInDTO
from src.application.exceptions import AuthError


class SignInUseCase:
    def __init__(self, port: ICognitoPort):
        self.port = port

    def execute(self, dto: SignInDTO) -> dict:
        if not dto.email or not dto.password:
            raise AuthError("Email and password are required")
        return self.port.sign_in(dto.email, dto.password)

