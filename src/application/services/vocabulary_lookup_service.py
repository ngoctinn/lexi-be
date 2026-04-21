from abc import ABC, abstractmethod

from domain.entities.vocabulary import Vocabulary


class VocabularyLookupService(ABC):
    """
    Cổng lấy dữ liệu từ vựng từ nguồn bên ngoài.

    Use case chỉ phụ thuộc vào abstraction này để giữ đúng clean architecture.
    """

    @abstractmethod
    def lookup(self, word: str) -> Vocabulary:
        """
        Lấy dữ liệu từ vựng đã chuẩn hóa từ nguồn ngoài.
        """
        ...
