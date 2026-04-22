from typing import List, Optional
from application.repositories.flash_card_repository import FlashCardRepository
from domain.entities.flashcard import FlashCard


class ListUserFlashcardsUC:
    """
    Ca sử dụng: Liệt kê tất cả thẻ từ vựng của người dùng với phân trang.
    
    Quy trình:
    1. Gọi repository để lấy danh sách thẻ với cursor-based pagination
    2. Trả về danh sách thẻ và cursor cho trang tiếp theo
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(
        self, user_id: str, last_key: Optional[dict], limit: int
    ) -> tuple[List[FlashCard], Optional[dict]]:
        """
        Thực thi trình tự lấy danh sách thẻ với phân trang.
        
        Returns:
            Tuple chứa (danh sách thẻ, cursor cho trang tiếp theo)
        """
        return self._repo.list_by_user(user_id, last_key, limit)
