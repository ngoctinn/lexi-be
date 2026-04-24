"""
Base presenter classes for formatting responses.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from interfaces.view_models.base import ErrorViewModel, OperationResult


class BasePresenter(ABC):
    """Base presenter for all presenters."""

    @abstractmethod
    def present_error(self, error_msg: str, code: Optional[str] = None) -> ErrorViewModel:
        """Format error response to ErrorViewModel."""
        pass

    @abstractmethod
    def present_success(self, data: Any, message: str = "Success") -> Dict[str, Any]:
        """Format success response to HTTP response."""
        pass
