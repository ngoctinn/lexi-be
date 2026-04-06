from typing import Dict
from application.dtos.flashcard.create.create_flashcard_command import CreateFlashCardCommand

class FlashCardMapper:
    def to_create_command(data: Dict):
        return CreateFlashCardCommand(
            word = data['word']
        )

