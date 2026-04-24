from abc import ABC, abstractmethod


class TranslationService(ABC):
    """Port (abstraction) cho dịch văn bản EN→VI."""

    @abstractmethod
    def translate_en_to_vi(self, text: str) -> str:
        """Dịch text từ tiếng Anh sang tiếng Việt. Trả về text gốc nếu lỗi."""
        ...
