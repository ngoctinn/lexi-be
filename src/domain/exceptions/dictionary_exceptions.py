"""Exceptions for Dictionary API integration."""


class WordNotFoundError(Exception):
    """Raised when word is not found in dictionary."""
    pass


class DictionaryServiceError(Exception):
    """Raised when dictionary service is unavailable or returns error."""
    pass


class DictionaryTimeoutError(Exception):
    """Raised when dictionary API request exceeds timeout limit."""
    pass
