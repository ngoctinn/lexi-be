from src.application.service_ports.auth_service import IAuthService
from src.application.dtos.auth_dto import ResetPasswordDTO
from application.exceptions.auth_errors import AuthError


class ResetPasswordUseCase:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    def execute(self, dto: ResetPasswordDTO):
        if len(dto.new_password) < 8:
            raise AuthError("Password must be at least 8 characters")
        self.auth_service.reset_password(dto.email, dto.code, dto.new_password)
