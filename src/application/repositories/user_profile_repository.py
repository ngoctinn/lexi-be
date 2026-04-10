from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.user_profile import UserProfile


class UserProfileRepository(ABC):
    """
    Giao diện cổng (Port) quản lý thông tin hồ sơ người học (UserProfile).
    
    Phục vụ cho luồng xác thực và cá nhân hóa trải nghiệm bài học.
    """

    @abstractmethod
    def create(self, profile: UserProfile) -> bool:
        """
        Đăng ký một hồ sơ người dùng mới trong hệ thống.
        
        Business Rule:
        - Hồ sơ phải gắn liền với định danh duy nhất (User ID) từ hệ thống Auth.
        
        Returns:
            bool: True nếu tạo mới thành công, False nếu đã tồn tại.
        """
        ...

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """
        Truy vấn hồ sơ cá nhân hóa người dùng.
        
        Sử dụng để lấy trình độ và giới tính giọng AI hiện tại.
        """
        ...

    @abstractmethod
    def update(self, profile: UserProfile) -> None:
        """
        Cập nhật lại các thông số cá nhân của người học.
        """
        ...
