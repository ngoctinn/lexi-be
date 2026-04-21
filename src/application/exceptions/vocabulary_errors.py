from application.exceptions.application_errors import ApplicationError


class VocabularyError(ApplicationError):
    """Lỗi gốc cho luồng dịch từ vựng."""


class VocabularyNotFoundError(VocabularyError):
    """Không tìm thấy từ trong nguồn tra cứu."""


class VocabularyLookupError(VocabularyError):
    """Lỗi khi gọi nguồn tra cứu hoặc dịch thuật bên ngoài."""


class VocabularyPersistenceError(VocabularyError):
    """Lỗi khi lưu cache từ vựng vào DynamoDB."""
