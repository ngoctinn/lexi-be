from src.application.service_ports.auth_service import IAuthService
from src.application.dtos.auth_dto import ConfirmSignUpDTO


class ConfirmSignUpUseCase:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    def execute(self, dto: ConfirmSignUpDTO):
        self.auth_service.confirm_sign_up(dto.email, dto.code)
