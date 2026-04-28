"""
Factory for creating handler instances.
Ensures consistent initialization and singleton pattern.
"""
from typing import Callable, TypeVar, Generic, Optional

T = TypeVar('T')


class HandlerFactory(Generic[T]):
    """
    Factory for lazy-loading handler dependencies.
    
    Ensures:
    - Dependencies initialized once per Lambda container
    - Consistent singleton pattern across all handlers
    - Easy testing (can inject mock dependencies)
    
    Usage:
        factory = HandlerFactory(build_my_controller)
        controller = factory.get()  # Lazy-loaded
    """

    def __init__(self, builder: Callable[[], T]):
        """
        Args:
            builder: Callable that builds the dependency
        """
        self.builder = builder
        self._instance: Optional[T] = None

    def get(self) -> T:
        """Get or build the dependency (singleton)."""
        if self._instance is None:
            self._instance = self.builder()
        return self._instance

    def reset(self) -> None:
        """Reset the singleton (useful for testing)."""
        self._instance = None
