from datetime import datetime

from application.dtos.flashcard.create.create_flashcard_command import CreateFlashCardCommand
from application.exceptions.flashcard_errors import InvalidUserId
from domain.entities.flashcard import FlashCard


class CreateFlashCardUC:
    def _init_(self, repo: IFlashCardRepo):
        self._repo = repo
    
    def execute(self, dto: CreateFlashCardCommand):
        # Kiểm tra xem Flashcard này đã tồn tại trong kho của User chưa
        # Theo thiết kế chúng ta bàn: PK: USER#<id>, SK: VOCAB#<word>
        existing_card = self._repo.get_by_user_and_word(dto.user_id, dto.vocab, dto.vocab_type)
        if existing_card:
            if existing_card:
                existing_card.definition_vi = dto.definition_vi
                existing_card.phonetic = dto.phonetic
                existing_card.audio_url = dto.audio_url
                existing_card.example_sentence = dto.example_sentence
                existing_card.word_type = dto.vocab_type
            
                # Cập nhật thời gian sửa đổi nếu bạn có trường updated_at
                existing_card.updated_at = datetime.now()

                # Lưu bản cập nhật
                return self._repo.save(existing_card)
        
        # Mapping từ DTO sang Domain Entity
        new_flashcard = FlashCard(
            user_id=dto.user_id,
            word=dto.vocab,
            word_type=dto.vocab_type,
            definition_vi=dto.definition_vi,
            phonetic=dto.phonetic,
            audio_url=dto.audio_url,
            example_sentence=dto.example_sentence,
            created_at=datetime.now(),
            next_review_at=datetime.now(), 
            level=1 
        )

        # Lưu vào Database thông qua Repository
        self._repo.save(new_flashcard)
        
        # Trả về kết quả (thường là entity hoặc một thông báo thành công)
        return new_flashcard
    
    # def __validate(dto: CreateFlashCardCommand):
    #     if not dto.user_id or not dto.user_id.strip():
    #         raise InvalidUserId("user_id không được để trống")
        
    #     if not dto.word or not dto.word.strip():
    #         raise InvalidVocab("từ không được để trống")
        
    #     if not dto.definition_vi or not dto.definition_vi.strip():
    #         raise InvalidDefinitionVI("nghĩa tiếng việt không được để trống")
        
    #     if not dto.phonetic or not dto.phonetic.strip():
    #         raise InvalidPhonetic("cách phát âm không được để trống")
        
    #     if not dto.audio_url or not dto.audio_url.strip():
    #         raise InvalidAudioUrl("đường dẫn audio không được để trống")

    #     if not dto.example_sentence or not dto.example_sentence.strip():
    #         raise InvalidExampleSentence("câu ví dụ không được để trống")
        
    #     if not dto.source_api or not dto.source_api.strip():
    #         raise InvalidSourceAPI("nguồn api không được để trống")
