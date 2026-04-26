"""Domain exceptions."""

from .dictionary_exceptions import (
    WordNotFoundError,
    DictionaryServiceError,
    DictionaryTimeoutError,
)

__all__ = ["WordNotFoundError", "DictionaryServiceError", "DictionaryTimeoutError"]
