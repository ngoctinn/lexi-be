from application.exceptions.application_errors import ApplicationError


class FlashCardError(ApplicationError):
    """Lớp ngoại lệ cơ bản cho các lỗi liên quan đến thẻ từ vựng."""
    pass

class FlashCardAlreadyExists(FlashCardError):
    """Lỗi khi thẻ từ vựng đã tồn tại cho người dùng này."""
    pass

class InvalidFlashCardData(FlashCardError):
    """Lỗi khi dữ liệu thẻ từ vựng không hợp lệ."""
    pass