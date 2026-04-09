import json

class FlashCardController:
    def __init__(self, create_flashcard_usecase) -> None:
        self.create_flashcard_usecase = create_flashcard_usecase

    def create(self, event) -> None:
        # mapping json to dto command
        body = json.loads(event.get('body', '{}'))
        command = self.mapper.to_create_command(body)

        # calling use case
        
        # return response