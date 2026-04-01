from src.application.ports.cognito_port import ICognitoPort
from src.application.dtos.auth_dto import RefreshTokenDTO


class RefreshTokenUseCase:
    def __init__(self, port: ICognitoPort):
        self.port = port

    def execute(self, dto: RefreshTokenDTO) -> dict:
        return self.port.refresh_token(dto.refresh_token)
