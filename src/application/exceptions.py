class AuthError(Exception):
    """Base exception cho tất cả auth errors — raise từ CognitoAdapter, catch tại Controller."""
    pass

class UserAlreadyExistsError(AuthError):
    """Email đã được đăng ký."""
    pass

class InvalidCredentialsError(AuthError):
    """Sai email hoặc password."""
    pass

class UserNotConfirmedError(AuthError):
    """Tài khoản chưa xác minh email."""
    pass

class CodeMismatchError(AuthError):
    """OTP/confirmation code không đúng."""
    pass

class UserNotFoundError(AuthError):
    """Không tìm thấy user."""
    pass

class ExpiredCodeError(AuthError):
    """OTP/confirmation code đã hết hạn."""
    pass
