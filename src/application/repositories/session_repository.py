from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.session import Session


class SessionRepository(ABC):
    """
    Giao diện cổng (Port) quản lý dữ liệu phiên học (Session).
    
    Phối hợp với Domain để lưu trữ trạng thái tiến trình học tập của người dùng.
    """

    @abstractmethod
    def save(self, session: Session) -> None:
        """
        Lưu trữ hoặc cập nhật thông tin phiên học vào hạ tầng bền vững.
        
        Business Rule:
        - Đảm bảo tính toàn vẹn của tiến trình học tập.
        - Xử lý ghi đè (Upsert) nếu session đã tồn tại.
        """
        ...

    @abstractmethod
    def get_by_id(self, session_id: str) -> Optional[Session]:
        """
        Tìm kiếm một phiên học cụ thể bằng định danh (ID).
        
        Sử dụng khi cần tiếp tục một phiên học đang dang dở hoặc xem lại lịch sử.
        """
        ...

    @abstractmethod
    def get_active_session(self, user_id: str) -> Optional[Session]:
        """
        Truy xuất phiên học đang hoạt động gần nhất của một người dùng.
        
        Business Rule:
        - Hệ thống cần xác định liệu người dùng có đang trong cuộc hội thoại nào chưa kết thúc không.
        """
        ...

    @abstractmethod
    def list_by_user(self, user_id: str, limit: int = 10) -> List[Session]:
        """
        Lấy danh sách các phiên học của người dùng để hiển thị lịch sử.
        """
        ...
