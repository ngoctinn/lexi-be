from dataclasses import dataclass, field
from typing import List


@dataclass
class Scenario:
    """Kịch bản hội thoại mẫu do hệ thống biên soạn."""
    # Định danh (ID)
    scenario_id: str                                    # ULID string

    # Nội dung kịch bản
    scenario_title: str = ""                            # Tiêu đề hiển thị cho người dùng
    context: str = ""                                   # Context label — dùng làm icon lookup key ở frontend
    roles: List[str] = field(default_factory=list)      # Đúng 2 vai (MVP) — source of truth duy nhất
    goals: List[str] = field(default_factory=list)      # Danh sách goal

    # Trạng thái
    is_active: bool = True
    usage_count: int = 0

    # Admin fields
    difficulty_level: str = ""                          # CEFR level khuyến nghị: A1/A2/B1/B2/C1/C2
    order: int = 0                                      # Thứ tự hiển thị trên lộ trình
    notes: str = ""                                     # Ghi chú nội bộ của Admin

    # Timestamps
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.scenario_title:
            raise ValueError("scenario_title không được để trống")
        self.roles = list(self.roles) if self.roles is not None else []
        self.goals = list(self.goals) if self.goals is not None else []

    def increment_usage(self):
        """Tăng bộ đếm lượt sử dụng."""
        self.usage_count += 1
        return self.usage_count

    def deactivate(self):
        """Ngừng kích hoạt kịch bản."""
        self.is_active = False

    def activate(self):
        """Kích hoạt lại kịch bản."""
        self.is_active = True

    def update_info(
        self,
        scenario_title: str = None,
        context: str = None,
        roles: list = None,
        goals: list = None,
        difficulty_level: str = None,
        order: int = None,
        notes: str = None,
        is_active: bool = None,
    ):
        """Cập nhật các field được phép — chỉ set nếu giá trị được cung cấp."""
        if scenario_title is not None:
            self.scenario_title = scenario_title
        if context is not None:
            self.context = context
        if roles is not None:
            self.roles = list(roles)
        if goals is not None:
            self.goals = list(goals)
        if difficulty_level is not None:
            self.difficulty_level = difficulty_level
        if order is not None:
            self.order = order
        if notes is not None:
            self.notes = notes
        if is_active is not None:
            self.is_active = is_active

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Scenario):
            return False
        return self.scenario_id == other.scenario_id

    def __hash__(self) -> int:
        return hash(self.scenario_id)
