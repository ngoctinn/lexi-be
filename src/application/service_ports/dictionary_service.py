"""Port (abstraction) for Dictionary API integration."""

from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.vocabulary import Vocabulary


class DictionaryService(ABC):
    """Port: Dictionary service abstraction for fetching word definitions."""

    @abstractmethod
    def get_word_definition(self, word: str, context: Optional[str] = None) -> Vocabulary:
        """
        Fetch word definition from dictionary.
        
        Args:
            word: English word or phrasal verb (e.g., "hello", "get off")
            context: Optional sentence containing the word for phrasal verb detection
        
        Returns:
            Vocabulary entity with phonetic, meanings, and audio URL
        
        Raises:
            WordNotFoundError: Word not found in dictionary
            DictionaryServiceError: External service unavailable or error
            DictionaryTimeoutError: Request exceeded timeout (30 seconds)
        """
        ...
