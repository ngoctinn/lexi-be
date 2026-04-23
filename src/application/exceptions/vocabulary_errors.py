from application.exceptions.application_errors import ApplicationError


class VocabularyError(ApplicationError):
    """Lớp ngoại lệ cơ bản cho các lỗi liên quan đến từ vựng."""
    pass


class VocabularyNotFoundError(VocabularyError):
    """Lỗi khi không tìm thấy từ vựng."""
    pass


class VocabularyLookupError(VocabularyError):
    """Lỗi khi tra cứu từ vựng thất bại (lỗi dịch vụ bên ngoài)."""
    pass


class VocabularyPersistenceError(VocabularyError):
    """Lỗi khi lưu trữ từ vựng thất bại."""
    pass
