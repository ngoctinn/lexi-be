import ulid
from application.dtos.flashcard.create.create_flashcard_command import CreateFlashCardCommand
from application.dtos.flashcard.create.create_flashcard_response import CreateFlashCardResponse
from application.repositories.flash_card_repository import FlashCardRepository
from domain.entities.flashcard import FlashCard
from shared.result import Result

class CreateFlashCardUC:
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
                flashcard_id=str(ulid.new()),
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
