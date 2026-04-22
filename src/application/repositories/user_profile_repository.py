from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from domain.entities.user_profile import UserProfile


class UserProfileRepository(ABC):
    """
    Giao diện cổng (Port) quản lý thông tin hồ sơ người học (UserProfile).
    """

    @abstractmethod
    def create(self, profile: UserProfile) -> bool:
        """
        Đăng ký một hồ sơ người dùng mới trong hệ thống.

        Returns:
            bool: True nếu tạo mới thành công, False nếu đã tồn tại.
        """
        ...

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Truy vấn hồ sơ cá nhân hóa người dùng."""
        ...

    @abstractmethod
    def update(self, profile: UserProfile) -> None:
        """Cập nhật lại các thông số cá nhân của người học."""
        ...

    @abstractmethod
    def list_learners(
        self, limit: int, last_key: Optional[dict]
    ) -> Tuple[List[UserProfile], Optional[dict]]:
        """Liệt kê tất cả learner với cursor-based pagination — dùng cho Admin."""
        ...
