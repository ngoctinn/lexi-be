"""
Flashcard-related view models.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FlashcardViewModel:
    """Flashcard view model for API responses."""
    flashcard_id: str
    word: str
    meaning: str
    example: str
    created_at: str
    next_review_at: str = ""


@dataclass(frozen=True)
class FlashcardListViewModel:
    """Flashcard list view model."""
    flashcards: list
    total_count: int
    next_key: dict | None = None
