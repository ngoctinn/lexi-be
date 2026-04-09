from typing import Generic, TypeVar, Optional, Any
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E')

@dataclass(frozen=True)
class Result(Generic[T, E]):
    """
    Result Pattern: Đóng gói kết quả thành công hoặc thất bại.
    Giúp tránh việc rò rỉ Exception ra các lớp ngoài.
    """
    is_success: bool
    value: Optional[T] = None
    error: Optional[E] = None

    @classmethod
    def success(cls, value: T) -> 'Result[T, E]':
        return cls(is_success=True, value=value)

    @classmethod
    def failure(cls, error: E) -> 'Result[T, E]':
        return cls(is_success=False, error=error)

    def __bool__(self) -> bool:
        return self.is_success
