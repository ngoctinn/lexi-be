"""Application service ports (abstractions)."""

from .translation_service import TranslationService
from .dictionary_service import DictionaryService

__all__ = ["TranslationService", "DictionaryService"]
