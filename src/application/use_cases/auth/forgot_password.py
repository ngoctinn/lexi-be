from src.application.ports.cognito_port import ICognitoPort
from src.application.dtos.auth_dto import ForgotPasswordDTO


class ForgotPasswordUseCase:
    def __init__(self, port: ICognitoPort):
        self.port = port

    def execute(self, dto: ForgotPasswordDTO):
        self.port.forgot_password(dto.email)
