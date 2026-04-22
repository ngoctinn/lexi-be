from application.repositories.flash_card_repository import FlashCardRepository
from domain.entities.flashcard import FlashCard


class ReviewFlashcardUC:
    """
    Ca sử dụng: Đánh giá mức độ nhớ thẻ từ vựng và cập nhật lịch ôn tập.
    
    Quy trình:
    1. Lấy thẻ từ repository theo user_id và flashcard_id
    2. Kiểm tra quyền sở hữu
    3. Áp dụng đánh giá SRS (forgot/hard/good/easy)
    4. Cập nhật thẻ vào database
    5. Trả về thẻ đã cập nhật
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(self, user_id: str, flashcard_id: str, rating: str) -> FlashCard:
        """
        Thực thi trình tự đánh giá thẻ từ vựng.
        
        Raises:
            KeyError: Nếu thẻ không tồn tại
            PermissionError: Nếu thẻ không thuộc về user
            ValueError: Nếu rating không hợp lệ
        """
        # 1. Lấy thẻ từ repository
        card = self._repo.get_by_user_and_id(user_id, flashcard_id)
        if card is None:
            raise KeyError(f"Flashcard {flashcard_id} not found")
        
        # 2. Kiểm tra quyền sở hữu
        if card.user_id != user_id:
            raise PermissionError("Forbidden")
        
        # 3. Áp dụng đánh giá SRS (raises ValueError nếu rating không hợp lệ)
        card.apply_review(rating)
        
        # 4. Cập nhật vào database
        self._repo.update(card)
        
        # 5. Trả về thẻ đã cập nhật
        return card
