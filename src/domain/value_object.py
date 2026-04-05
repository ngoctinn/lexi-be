from dataclasses import dataclass

@dataclass(frozen=True)
class ValueObject:
    """
    Lớp cơ sở cho các Value Objects trong Domain.
    Các đối tượng này được định danh bằng chính các giá trị thuộc tính của chúng.
    """
    pass
