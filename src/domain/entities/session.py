from dataclasses import dataclass, field
from ulid import ULID
from domain.value_objects.enums import Gender, ProficiencyLevel

@dataclass
class Session:
    """Phiên hội thoại (Session) đang diễn ra giữa AI và Người dùng."""
    # Định danh (ID)
    session_id: ULID # ID duy nhất của phiên học

    # Cấu hình phiên
    scenario_id: ULID           # ID kịch bản đang học
    user_id: str = ""                # ID người dùng tham gia
    learner_role_id: str = ""        # Vai người học đã chọn trong session
    ai_role_id: str = ""             # Vai AI đã nhận trong session
    ai_gender: Gender = Gender.FEMALE # Giới tính của giọng nói AI
    level: ProficiencyLevel = ProficiencyLevel.B1 # Trình độ ngoại ngữ của session
    selected_goals: list[str] = field(default_factory=list)
    # Snapshot: final built prompt used to run the session (serialize as plain string)
    prompt_snapshot: str = ""      # Lưu prompt hoàn chỉnh để replay/debug
    status: str = "ACTIVE"         # Trạng thái phiên học

    # Chỉ số thống kê
    total_turns: int = 0             # Tổng số lượt thoại trong session
    user_turns: int = 0              # Số lượt thoại của người dùng
    hint_used_count: int = 0         # Số lần người dùng đã nhận hỗ trợ (gợi ý)
    connection_id: str = ""         # Kết nối websocket nếu session đang online
    created_at: str = ""            # Thời điểm tạo session
    updated_at: str = ""            # Thời điểm cập nhật gần nhất

    def __post_init__(self):
        if not self.user_id or not self.scenario_id:
            raise ValueError("user_id và scenario_id là bắt buộc để mở Session")
        self.selected_goals = list(self.selected_goals) if self.selected_goals is not None else []

    def increment_turns(self, is_user: bool = True):
        """Ghi nhận lượt thoại mới vào session."""
        self.total_turns += 1
        if is_user:
            self.user_turns += 1

    def record_hint(self):
        """Ghi nhận việc sử dụng giải thích ngữ pháp/gợi ý."""
        self.hint_used_count += 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Session):
            return False
        return self.session_id == other.session_id

    def __hash__(self) -> int:
        return hash(self.session_id)
