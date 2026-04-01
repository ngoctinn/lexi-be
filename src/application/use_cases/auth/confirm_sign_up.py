from src.application.ports.cognito_port import ICognitoPort
from src.application.dtos.auth_dto import ConfirmSignUpDTO


class ConfirmSignUpUseCase:
    def __init__(self, port: ICognitoPort):
        self.port = port

    def execute(self, dto: ConfirmSignUpDTO):
        self.port.confirm_sign_up(dto.email, dto.code)
