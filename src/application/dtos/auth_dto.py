from dataclasses import dataclass


@dataclass
class SignUpDTO:
    email: str
    password: str


@dataclass
class ConfirmSignUpDTO:
    email: str
    code: str


@dataclass
class SignInDTO:
    email: str
    password: str


@dataclass
class RefreshTokenDTO:
    refresh_token: str


@dataclass
class ForgotPasswordDTO:
    email: str


@dataclass
class ResetPasswordDTO:
    email: str
    code: str
    new_password: str


@dataclass
class SignOutDTO:
    access_token: str


@dataclass
class CreateUserProfileDTO:
    user_id: str
    email: str
