from src.application.service_ports.auth_service import IAuthService
from src.application.dtos.auth_dto import ForgotPasswordDTO


class ForgotPasswordUseCase:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    def execute(self, dto: ForgotPasswordDTO):
        self.auth_service.forgot_password(dto.email)
