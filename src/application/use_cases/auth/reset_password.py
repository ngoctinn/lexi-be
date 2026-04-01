from src.application.ports.cognito_port import ICognitoPort
from src.application.dtos.auth_dto import ResetPasswordDTO
from src.application.exceptions import AuthError


class ResetPasswordUseCase:
    def __init__(self, port: ICognitoPort):
        self.port = port

    def execute(self, dto: ResetPasswordDTO):
        if len(dto.new_password) < 8:
            raise AuthError("Password must be at least 8 characters")
        self.port.reset_password(dto.email, dto.code, dto.new_password)
