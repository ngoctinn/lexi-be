from application.dtos.flashcard.create.create_flashcard_command import CreateFlashCardCommand
from application.exceptions.flashcard_errors import InvalidUserId


class CreateFlashCardUC:
    def _init_(self, repo: IFlashCardRepo):
        self._repo = repo
    
    def execute(self, dto: CreateFlashCardCommand):
        # validate
        
        # map dto command to entity
        # business logic
        # save database
        # map entity to dto response
        flashcard = FlashCard(front, back)
        return self._repo.save(flashcard)
    
    def __validate(dto: CreateFlashCardCommand):
        if not dto.user_id or not dto.user_id.strip():
            raise InvalidUserId("user_id không được để trống")
        
        if not dto.word or not dto.word.strip():
            raise InvalidVocab("từ không được để trống")
        
        if not dto.definition_vi or not dto.definition_vi.strip():
            raise InvalidDefinitionVI("nghĩa tiếng việt không được để trống")
        
        if not dto.phonetic or not dto.phonetic.strip():
            raise InvalidPhonetic("cách phát âm không được để trống")
        
        if not dto.audio_url or not dto.audio_url.strip():
            raise InvalidAudioUrl("đường dẫn audio không được để trống")

        if not dto.example_sentence or not dto.example_sentence.strip():
            raise InvalidExampleSentence("câu ví dụ không được để trống")
        
        if not dto.source_api or not dto.source_api.strip():
            raise InvalidSourceAPI("nguồn api không được để trống")
