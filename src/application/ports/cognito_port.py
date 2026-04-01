from abc import ABC, abstractmethod


class ICognitoPort(ABC):
    @abstractmethod
    def sign_up(self, email: str, password: str): ...

    @abstractmethod
    def confirm_sign_up(self, email: str, code: str): ...

    @abstractmethod
    def sign_in(self, email: str, password: str) -> dict: ...

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> dict: ...

    @abstractmethod
    def forgot_password(self, email: str): ...

    @abstractmethod
    def reset_password(self, email: str, code: str, new_password: str): ...

    @abstractmethod
    def sign_out(self, access_token: str): ...
