from abc import ABC, abstractmethod
from typing import List
from domain.entities.scoring import Scoring


class ScoringRepository(ABC):
    """
    Giao diện cổng (Port) quản lý hồ sơ đánh giá và điểm số (Scoring).
    
    Ghi nhận phản hồi chi tiết về phát âm, ngữ pháp và độ trôi chảy.
    """

    @abstractmethod
    def save(self, score: Scoring) -> None:
        """
        Ghi nhận kết quả chấm điểm của một lượt hội thoại.
        
        Business Rule:
        - Đồng bộ kết quả này phục vụ cho việc tính toán tổng điểm session.
        """
        ...

    @abstractmethod
    def get_by_session(self, session_id: str) -> List[Scoring]:
        """
        Truy xuất dữ liệu đánh giá của toàn bộ một phiên hội thoại.
        """
        ...

    @abstractmethod
    def get_user_progress(self, user_id: str, limit: int = 50) -> List[Scoring]:
        """
        Lấy thống kê điểm số dài hạn của một người dùng.
        """
        ...
