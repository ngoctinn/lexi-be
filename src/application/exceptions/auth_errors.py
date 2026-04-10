from application.exceptions.application_errors import ApplicationError

class AuthError(ApplicationError):
    """Lớp ngoại lệ cơ bản cho các lỗi xác thực và phân quyền."""
    pass

class UserNotFoundError(AuthError):
    """Lỗi xảy ra khi không tìm thấy hồ sơ người dùng trong hệ thống."""
    pass

