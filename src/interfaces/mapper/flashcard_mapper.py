from typing import Dict
from application.dtos.flashcard.create.create_flashcard_command import CreateFlashCardCommand

class FlashCardMapper:
    def to_create_command(data: Dict):
        return CreateFlashCardCommand(
            user_id = data['user_id'],
            word = data['word'],
            word_type = data['word_type'],
            definition_vi = data['definition_vi'],
            phonetic = data['phonetic'],
            audio_url = data['audio_url'],
            example_sentence = data['example_sentence'],
            source_api = data['source_api']
        )

