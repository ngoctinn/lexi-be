from src.shared.http_utils import parse_body, require_fields
from src.interfaces.presenters.auth_presenter import AuthPresenter
from src.application.use_cases.auth.sign_up import SignUpUseCase
from src.application.use_cases.auth.confirm_sign_up import ConfirmSignUpUseCase
from src.application.use_cases.auth.sign_in import SignInUseCase
from src.application.use_cases.auth.refresh_token import RefreshTokenUseCase
from src.application.use_cases.auth.forgot_password import ForgotPasswordUseCase
from src.application.use_cases.auth.reset_password import ResetPasswordUseCase
from src.application.use_cases.auth.sign_out import SignOutUseCase
from src.application.dtos.auth_dto import (
    SignUpDTO, ConfirmSignUpDTO, SignInDTO, RefreshTokenDTO,
    ForgotPasswordDTO, ResetPasswordDTO, SignOutDTO,
)
from src.application.exceptions import AuthError


class AuthController:
    def __init__(
        self,
        sign_up: SignUpUseCase,
        confirm_sign_up: ConfirmSignUpUseCase,
        sign_in: SignInUseCase,
        refresh_token: RefreshTokenUseCase,
        forgot_password: ForgotPasswordUseCase,
        reset_password: ResetPasswordUseCase,
        sign_out: SignOutUseCase,
    ):
        self.sign_up = sign_up
        self.confirm_sign_up = confirm_sign_up
        self.sign_in = sign_in
        self.refresh_token = refresh_token
        self.forgot_password = forgot_password
        self.reset_password = reset_password
        self.sign_out = sign_out

    def handle_sign_up(self, event):
        try:
            body = parse_body(event)
            require_fields(body, "email", "password")
        except ValueError as e:
            return AuthPresenter.error(str(e))
        try:
            self.sign_up.execute(SignUpDTO(email=body["email"], password=body["password"]))
            return AuthPresenter.success("User created. Check email for confirmation code.", 201)
        except AuthError as e:
            return AuthPresenter.error(str(e))

    def handle_confirm_sign_up(self, event):
        try:
            body = parse_body(event)
            require_fields(body, "email", "code")
        except ValueError as e:
            return AuthPresenter.error(str(e))
        try:
            self.confirm_sign_up.execute(ConfirmSignUpDTO(email=body["email"], code=body["code"]))
            return AuthPresenter.success("Account confirmed.")
        except AuthError as e:
            return AuthPresenter.error(str(e))

    def handle_sign_in(self, event):
        try:
            body = parse_body(event)
            require_fields(body, "email", "password")
        except ValueError as e:
            return AuthPresenter.error(str(e))
        try:
            tokens = self.sign_in.execute(SignInDTO(email=body["email"], password=body["password"]))
            return AuthPresenter.tokens(tokens)
        except AuthError as e:
            return AuthPresenter.error(str(e), 401)

    def handle_refresh_token(self, event):
        try:
            body = parse_body(event)
            require_fields(body, "refresh_token")
        except ValueError as e:
            return AuthPresenter.error(str(e))
        try:
            tokens = self.refresh_token.execute(RefreshTokenDTO(refresh_token=body["refresh_token"]))
            return AuthPresenter.tokens(tokens)
        except AuthError as e:
            return AuthPresenter.error(str(e), 401)

    def handle_forgot_password(self, event):
        try:
            body = parse_body(event)
            require_fields(body, "email")
        except ValueError as e:
            return AuthPresenter.error(str(e))
        try:
            self.forgot_password.execute(ForgotPasswordDTO(email=body["email"]))
            return AuthPresenter.success("Password reset code sent to email.")
        except AuthError as e:
            return AuthPresenter.error(str(e))

    def handle_reset_password(self, event):
        try:
            body = parse_body(event)
            require_fields(body, "email", "code", "new_password")
        except ValueError as e:
            return AuthPresenter.error(str(e))
        try:
            self.reset_password.execute(ResetPasswordDTO(
                email=body["email"], code=body["code"], new_password=body["new_password"]
            ))
            return AuthPresenter.success("Password reset successful.")
        except AuthError as e:
            return AuthPresenter.error(str(e))

    def handle_sign_out(self, event):
        try:
            body = parse_body(event)
            require_fields(body, "access_token")
        except ValueError as e:
            return AuthPresenter.error(str(e))
        try:
            self.sign_out.execute(SignOutDTO(access_token=body["access_token"]))
            return AuthPresenter.success("Signed out successfully.")
        except AuthError as e:
            return AuthPresenter.error(str(e), 401)
