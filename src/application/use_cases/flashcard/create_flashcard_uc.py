from application.dtos.flashcard.create.create_flashcard_command import CreateFlashCardCommand


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
