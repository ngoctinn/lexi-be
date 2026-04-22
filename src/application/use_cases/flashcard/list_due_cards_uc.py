from typing import List
from application.repositories.flash_card_repository import FlashCardRepository
from domain.entities.flashcard import FlashCard


class ListDueCardsUC:
    """
    Ca sử dụng: Liệt kê các thẻ từ vựng đến hạn ôn tập.
    
    Quy trình:
    1. Gọi repository để lấy danh sách thẻ có next_review_at <= now
    2. Trả về danh sách thẻ
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(self, user_id: str) -> List[FlashCard]:
        """
        Thực thi trình tự lấy danh sách thẻ đến hạn.
        """
        return self._repo.list_due_cards(user_id)
