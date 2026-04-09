from abc import ABC, abstractmethod
from typing import List
from domain.entities.turn import Turn


class TurnRepository(ABC):
    """
    Giao diện cổng (Port) quản lý dữ liệu các lượt thoại (Turn).
    
    Phụ trách việc lưu trữ dòng thời gian (Timeline) của cuộc hội thoại.
    """

    @abstractmethod
    def save(self, turn: Turn) -> None:
        """
        Ghi nhận một lượt thoại mới vào hệ thống dữ liệu.
        
        Business Rule:
        - Mỗi lượt thoại phải được lưu trữ ngay lập tức để duy trì tính nhất quán.
        """
        ...

    @abstractmethod
    def list_by_session(self, session_id: str) -> List[Turn]:
        """
        Truy xuất toàn bộ lịch sử hội thoại của một phiên học.
        
        Sử dụng khi AI cần đọc lại lịch sử để lấy context phục vụ phản hồi.
        """
        ...

    @abstractmethod
    def delete_by_session(self, session_id: str) -> None:
        """
        Xóa sạch các lượt thoại của một session cụ thể.
        
        Business Rule:
        - Sử dụng để dọn dẹp hoặc đặt lại phiên hội thoại (Reset).
        """
        ...
