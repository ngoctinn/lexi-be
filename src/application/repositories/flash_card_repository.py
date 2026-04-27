from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.flashcard import FlashCard


class FlashCardRepository(ABC):
    """
    Giao diện cổng (Port) quản lý dữ liệu thẻ từ vựng (FlashCard).
    
    Phục vụ thuật toán ghi nhớ lặp lại ngắt quãng (SRS) cho người học.
    """

    @abstractmethod
    def save(self, card: FlashCard) -> None:
        """
        Lưu trữ hoặc đồng bộ trạng thái thẻ từ vựng hiện tại.
        
        Business Rule:
        - Hệ thống cần ghi nhận ngay kết quả đánh giá để tính toán SRS cho lần tới.
        """
        ...

    @abstractmethod
    def get_by_id(self, flashcard_id: str) -> Optional[FlashCard]:
        """Truy xuất một thẻ cụ thể để xem lại thông tin chi tiết."""
        ...

    @abstractmethod
    def list_due_cards(self, user_id: str) -> List[FlashCard]:
        """
        Tìm kiếm danh sách thẻ đã đến thời điểm cần ôn tập.
        
        Business Rule:
        - Dựa trên trường `next_review_at` để lọc dữ liệu ôn tập mỗi ngày.
        """
        ...

    @abstractmethod
    def get_by_user_and_word(self, user_id: str, word: str) -> Optional[FlashCard]:
        """
        Xác định xem người dùng đã tạo thẻ ghi nhớ cho từ vựng này chưa.
        """
        ...

    @abstractmethod
    def get_by_user_and_id(self, user_id: str, flashcard_id: str) -> Optional[FlashCard]:
        """Lấy thẻ theo user_id + flashcard_id (dùng PK + SK trực tiếp)."""
        ...

    @abstractmethod
    def list_by_user(
        self, user_id: str, last_key: Optional[dict], limit: int
    ) -> tuple[list[FlashCard], Optional[dict]]:
        """Liệt kê tất cả thẻ của user với cursor-based pagination."""
        ...

    @abstractmethod
    def update(self, card: FlashCard) -> None:
        """Cập nhật thẻ đã tồn tại (bao gồm GSI2SK)."""
        ...

    @abstractmethod
    def update_content(
        self,
        user_id: str,
        flashcard_id: str,
        translation_vi: Optional[str] = None,
        phonetic: Optional[str] = None,
        audio_url: Optional[str] = None,
        example_sentence: Optional[str] = None
    ) -> FlashCard:
        """
        Update only content fields while preserving SRS data.
        
        Supports updating: translation_vi, phonetic, audio_url, example_sentence
        Preserves: ease_factor, repetition_count, interval_days, next_review_at
        """
        ...

    @abstractmethod
    def delete(self, user_id: str, flashcard_id: str) -> bool:
        """Delete a flashcard. Returns True if successful."""
        ...
