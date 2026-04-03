from src.application.service_ports.auth_service import IAuthService
from src.application.dtos.auth_dto import RefreshTokenDTO


class RefreshTokenUseCase:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    def execute(self, dto: RefreshTokenDTO) -> dict:
        return self.auth_service.refresh_token(dto.refresh_token)
