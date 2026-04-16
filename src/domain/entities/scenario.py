from dataclasses import dataclass, field
from typing import List
from ulid import ULID

@dataclass
class Scenario:
    """Kịch bản hội thoại mẫu do hệ thống biên soạn."""
    # Định danh (ID)
    scenario_id: ULID # ID duy nhất của kịch bản

    # Nội dung kịch bản
    scenario_title: str = ""         # Tiêu đề hiển thị cho người dùng
    context: str = ""                # Context label (e.g. 'cafe', 'interview')
    my_character: str = ""           # Nhân vật người dùng sẽ đóng vai
    ai_character: str = ""           # Nhân vật AI sẽ đóng vai
    goals: List[str] = field(default_factory=list)      # Danh sách goal (e.g. order drink)
    user_roles: List[str] = field(default_factory=list) # Các vai trò người dùng có thể chọn
    ai_roles: List[str] = field(default_factory=list)   # Các vai trò AI có thể đóng

    # Trạng thái
    is_active: bool = True           # Kịch bản có đang được sử dụng hay không
    usage_count: int = 0             # Số phiên đã dùng kịch bản này

    def __post_init__(self):
        # Kiểm tra tính toàn vẹn dữ liệu bắt buộc
        if not self.scenario_title:
            raise ValueError("scenario_title không được để trống")
        # Chuẩn hóa: đảm bảo các danh sách là danh sách chuỗi
        self.goals = list(self.goals) if self.goals is not None else []
        self.user_roles = list(self.user_roles) if self.user_roles is not None else []
        self.ai_roles = list(self.ai_roles) if self.ai_roles is not None else []

    def increment_usage(self):
        """Tăng bộ đếm lượt sử dụng."""
        self.usage_count += 1
        return self.usage_count

    def deactivate(self):
        """Ngừng kích hoạt kịch bản."""
        self.is_active = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Scenario):
            return False
        return self.scenario_id == other.scenario_id

    def __hash__(self) -> int:
        return hash(self.scenario_id)
