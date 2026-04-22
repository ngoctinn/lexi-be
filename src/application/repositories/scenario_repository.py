from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.scenario import Scenario


class ScenarioRepository(ABC):
    """
    Giao diện cổng (Port) quản lý danh mục kịch bản hội thoại (Scenario).
    """

    @abstractmethod
    def list_active(self) -> List[Scenario]:
        """Lấy danh sách các kịch bản đang active — dùng cho Learner."""
        ...

    @abstractmethod
    def list_all(self) -> List[Scenario]:
        """Lấy tất cả kịch bản kể cả inactive — dùng cho Admin."""
        ...

    @abstractmethod
    def get_by_id(self, scenario_id: str) -> Optional[Scenario]:
        """Truy xuất thông tin chi tiết một kịch bản."""
        ...

    @abstractmethod
    def save(self, scenario: Scenario) -> None:
        """Upsert kịch bản — dùng để tăng usage_count."""
        ...

    @abstractmethod
    def create(self, scenario: Scenario) -> None:
        """Tạo kịch bản mới — fail nếu đã tồn tại."""
        ...

    @abstractmethod
    def update(self, scenario: Scenario) -> None:
        """Cập nhật kịch bản đã tồn tại."""
        ...
