from src.application.service_ports.auth_service import IAuthService
from src.application.dtos.auth_dto import SignOutDTO
from application.exceptions.auth_errors import AuthError


class SignOutUseCase:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    def execute(self, dto: SignOutDTO):
        if not dto.access_token:
            raise AuthError("Access token is required")
        self.auth_service.sign_out(dto.access_token)

