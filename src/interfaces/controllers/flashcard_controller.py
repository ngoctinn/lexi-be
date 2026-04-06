import json
from typing import Dict

from interfaces.mapper.flashcard_mapper import FlashCardMapper


class FlashCardController:
    def __init__(self, mapper: FlashCardMapper, create_flashcard_usecase) -> None:
        self.mapper = mapper
        self.create_flashcard_usecase = create_flashcard_usecase

    def create(self, event) -> None:
        # mapping json to dto command
        body = json.loads(event.get('body', '{}'))
        command = self.mapper.to_create_command(body)

        # calling use case

        # return response