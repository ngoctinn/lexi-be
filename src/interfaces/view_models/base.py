"""
Base view models for API responses.
"""

from dataclasses import dataclass
from typing import Optional, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ErrorViewModel:
    """Error response view model."""
    message: str
    code: Optional[str] = None


@dataclass(frozen=True)
class SuccessViewModel:
    """Generic success response view model."""
    data: dict
    message: str = "Success"


@dataclass
class OperationResult(Generic[T]):
    """Represents the result of an operation (Either pattern).
    
    Can be either success with a value or failure with an error.
    """
    _success: Optional[T] = None
    _error: Optional[ErrorViewModel] = None

    def __init__(self, success: Optional[T] = None, error: Optional[ErrorViewModel] = None):
        """Initialize with either success or error, but not both."""
        if (success is None and error is None) or (success is not None and error is not None):
            raise ValueError("Either success or error must be provided, but not both")
        object.__setattr__(self, '_success', success)
        object.__setattr__(self, '_error', error)

    @property
    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self._success is not None

    @property
    def success(self) -> T:
        """Get success value."""
        if self._success is None:
            raise ValueError("Cannot access success value on error result")
        return self._success

    @property
    def error(self) -> ErrorViewModel:
        """Get error value."""
        if self._error is None:
            raise ValueError("Cannot access error value on success result")
        return self._error

    @classmethod
    def succeed(cls, value: T) -> "OperationResult[T]":
        """Create successful result."""
        return cls(success=value)

    @classmethod
    def fail(cls, message: str, code: Optional[str] = None) -> "OperationResult[T]":
        """Create failed result."""
        return cls(error=ErrorViewModel(message, code))
