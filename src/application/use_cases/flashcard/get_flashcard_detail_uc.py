from application.repositories.flash_card_repository import FlashCardRepository
from domain.entities.flashcard import FlashCard


class GetFlashcardDetailUC:
    """
    Ca sử dụng: Lấy thông tin chi tiết của một thẻ từ vựng.
    
    Quy trình:
    1. Lấy thẻ từ repository theo user_id và flashcard_id
    2. Kiểm tra quyền sở hữu
    3. Trả về thẻ
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(self, user_id: str, flashcard_id: str) -> FlashCard:
        """
        Thực thi trình tự lấy chi tiết thẻ từ vựng.
        
        Raises:
            KeyError: Nếu thẻ không tồn tại
            PermissionError: Nếu thẻ không thuộc về user
        """
        # 1. Lấy thẻ từ repository
        card = self._repo.get_by_user_and_id(user_id, flashcard_id)
        if card is None:
            raise KeyError(f"Flashcard {flashcard_id} not found")
        
        # 2. Kiểm tra quyền sở hữu
        if card.user_id != user_id:
            raise PermissionError("Forbidden")
        
        # 3. Trả về thẻ
        return card
