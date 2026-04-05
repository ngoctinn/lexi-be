from dataclasses import dataclass, field
from ulid import ULID
from .enums import ProficiencyLevel, Gender

@dataclass
class Session:
    """Phiên hội thoại (Session) đang diễn ra giữa AI và Người dùng."""
    # Định danh (ID)
    session_id: str = field(default_factory=lambda: str(ULID()), init=False) # ID duy nhất của phiên học
    
    # Cấu hình phiên
    user_id: str = ""                # ID người dùng tham gia
    scenario_id: str = ""            # ID kịch bản đang học
    ai_gender: Gender = Gender.FEMALE # Giới tính của giọng nói AI
    level: ProficiencyLevel = ProficiencyLevel.B1 # Trình độ ngoại ngữ của session
    
    # Chỉ số thống kê
    total_turns: int = 0             # Tổng số lượt thoại trong session
    user_turns: int = 0              # Số lượt thoại của người dùng
    hint_used_count: int = 0         # Số lần người dùng đã nhận hỗ trợ (gợi ý)

    def __post_init__(self):
        if not self.user_id or not self.scenario_id:
            raise ValueError("user_id và scenario_id là bắt buộc để mở Session")

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
