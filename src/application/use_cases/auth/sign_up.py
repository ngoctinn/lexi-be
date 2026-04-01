import re
from src.application.ports.cognito_port import ICognitoPort
from src.application.dtos.auth_dto import SignUpDTO
from src.application.exceptions import AuthError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignUpUseCase:
    def __init__(self, port: ICognitoPort):
        self.port = port

    def execute(self, dto: SignUpDTO):
        if not _EMAIL_RE.match(dto.email):
            raise AuthError("Invalid email format")
        if len(dto.password) < 8:
            raise AuthError("Password must be at least 8 characters")
        self.port.sign_up(dto.email, dto.password)
