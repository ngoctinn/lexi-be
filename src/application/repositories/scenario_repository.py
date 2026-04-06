from abc import ABC, abstractmethod
from typing import Optional, List
from src.domain.entities.scenario import Scenario


class ScenarioRepository(ABC):
    """
    Giao diện cổng (Port) quản lý danh mục kịch bản hội thoại (Scenario).
    
    Hỗ trợ AI và Người dùng chọn lựa bối cảnh luyện tập đúng trình độ.
    """

    @abstractmethod
    def list_active(self) -> List[Scenario]:
        """
        Lấy danh sách các kịch bản đang được kích hoạt học tập.
        
        Business Rule:
        - Hệ thống chỉ lọc các bài học có trạng thái `is_active = True`.
        """
        ...

    @abstractmethod
    def get_by_id(self, scenario_id: str) -> Optional[Scenario]:
        """Truy xuất thông tin chi tiết một kịch bản luyện tập."""
        ...

    @abstractmethod
    def save(self, scenario: Scenario) -> None:
        """
        Lưu trữ hoặc cập nhật thống kê cho kịch bản.
        
        Business Rule:
        - Dùng để tăng `usage_count` hoặc điều chỉnh Prompt bởi quản trị viên.
        """
        ...
