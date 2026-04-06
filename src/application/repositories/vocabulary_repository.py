from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.vocabulary import Vocabulary


class VocabularyRepository(ABC):
    """
    Giao diện cổng (Port) quản lý kho lưu trữ từ điển hệ thống (Vocabulary).
    
    Hỗ trợ AI và Người dùng tra cứu thông tin ngôn ngữ chính thức.
    """

    @abstractmethod
    def find_by_word(self, word: str) -> Optional[Vocabulary]:
        """
        Truy xuất thông tin từ vựng định danh bằng chính từ đó (word).
        
        Business Rule:
        - Word dùng làm Partition Key trong WordCache.
        """
        ...

    @abstractmethod
    def list_by_level(self, level: str, limit: int = 20) -> List[Vocabulary]:
        """
        Gợi ý danh sách từ vựng theo trình độ CERF mục tiêu.
        """
        ...
