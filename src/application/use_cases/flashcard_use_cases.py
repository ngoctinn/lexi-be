"""Flashcard Use Cases - Consolidated from individual files."""

from typing import List, Optional
from ulid import ULID
from application.dtos.flashcard.create.create_flashcard_command import CreateFlashCardCommand
from application.dtos.flashcard.create.create_flashcard_response import CreateFlashCardResponse
from application.repositories.flash_card_repository import FlashCardRepository
from domain.entities.flashcard import FlashCard
from shared.result import Result


class CreateFlashCardUseCase:
    """
    Ca sử dụng: Tạo thẻ từ vựng (FlashCard) mới cho người dùng.
    
    Quy trình:
    1. Kiểm tra từ vựng đã tồn tại trong kho thẻ của người dùng chưa.
    2. Nếu chưa, tạo thực thể FlashCard mới với ID duy nhất (ULID).
    3. Lưu vào cơ sở dữ liệu thông qua Repository.
    4. Trả về kết quả thành công kèm thông tin thẻ.
    """
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(self, command: CreateFlashCardCommand) -> Result[CreateFlashCardResponse, str]:
        """
        Thực thi trình tự tạo thẻ ghi nhớ.
        """
        # 1. Kiểm tra trùng lặp (Idempotency check)
        existing_card = self._repo.get_by_user_and_word(command.user_id, command.vocab)
        if existing_card:
            return Result.failure(f"Từ vựng '{command.vocab}' đã có trong kho thẻ của bạn.")

        # 2. Tạo thực thể Domain mới
        try:
            flashcard = FlashCard(
                flashcard_id=str(ULID()),
                user_id=command.user_id,
                word=command.vocab,
                translation_vi=command.translation_vi or "",
                definition_vi=command.definition_vi,
                phonetic=command.phonetic or "",
                audio_url=command.audio_url or "",
                example_sentence=command.example_sentence or "",
                source_session_id=command.source_session_id,
                source_turn_index=command.source_turn_index,
            )
        except ValueError as e:
            return Result.failure(str(e))

        # 3. Lưu trữ
        try:
            self._repo.save(flashcard)
        except Exception as e:
            return Result.failure(f"Không thể lưu thẻ từ vựng: {str(e)}")

        # 4. Trả về kết quả
        response = CreateFlashCardResponse(
            flashcard_id=flashcard.flashcard_id,
            word=flashcard.word,
            message="Tạo thẻ từ vựng thành công."
        )
        return Result.success(response)


class GetFlashcardDetailUseCase:
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


class ListDueCardsUseCase:
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


class ListUserFlashcardsUseCase:
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


class ReviewFlashcardUseCase:
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
