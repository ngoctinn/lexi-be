from src.application.service_ports.auth_service import IAuthService
from src.application.dtos.auth_dto import SignInDTO
from src.application.exceptions import AuthError


class SignInUseCase:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    def execute(self, dto: SignInDTO) -> dict:
        if not dto.email or not dto.password:
            raise AuthError("Email and password are required")
        return self.auth_service.sign_in(dto.email, dto.password)

