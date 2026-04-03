import re
from src.application.service_ports.auth_service import IAuthService
from src.application.dtos.auth_dto import SignUpDTO
from src.application.exceptions import AuthError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignUpUseCase:
    def __init__(self, auth_service: IAuthService):
        self.auth_service = auth_service

    def execute(self, dto: SignUpDTO):
        if not _EMAIL_RE.match(dto.email):
            raise AuthError("Invalid email format")
        if len(dto.password) < 8:
            raise AuthError("Password must be at least 8 characters")
        self.auth_service.sign_up(dto.email, dto.password)
