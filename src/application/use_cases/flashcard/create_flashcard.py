class CreateFlashCard:
    def _init_(self, repo: IFlashCardRepo):
        self._repo = repo
    
    def execute(self, front, back):
        flashcard = FlashCard(front, back)
        return self._repo.save(flashcard)
