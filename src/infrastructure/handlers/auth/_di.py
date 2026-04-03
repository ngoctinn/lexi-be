from src.infrastructure.auth.cognito_adapter import CognitoAdapter
from src.infrastructure.persistence.dynamo_user_repo import DynamoDBUserRepo
from src.application.use_cases.auth.sign_up import SignUpUseCase
from src.application.use_cases.auth.confirm_sign_up import ConfirmSignUpUseCase
from src.application.use_cases.auth.sign_in import SignInUseCase
from src.application.use_cases.auth.refresh_token import RefreshTokenUseCase
from src.application.use_cases.auth.forgot_password import ForgotPasswordUseCase
from src.application.use_cases.auth.reset_password import ResetPasswordUseCase
from src.application.use_cases.auth.sign_out import SignOutUseCase
from src.application.use_cases.auth.create_user_profile import CreateUserProfileUseCase
from src.interfaces.controllers.auth_controller import AuthController


def build_auth_controller() -> AuthController:
    adapter = CognitoAdapter()
    return AuthController(
        sign_up=SignUpUseCase(auth_service=adapter),
        confirm_sign_up=ConfirmSignUpUseCase(auth_service=adapter),
        sign_in=SignInUseCase(auth_service=adapter),
        refresh_token=RefreshTokenUseCase(auth_service=adapter),
        forgot_password=ForgotPasswordUseCase(auth_service=adapter),
        reset_password=ResetPasswordUseCase(auth_service=adapter),
        sign_out=SignOutUseCase(auth_service=adapter),
    )


def build_post_confirmation_use_case() -> CreateUserProfileUseCase:
    return CreateUserProfileUseCase(repo=DynamoDBUserRepo())
