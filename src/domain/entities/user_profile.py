from dataclasses import dataclass

from domain.value_objects.enums import ProficiencyLevel, Role

@dataclass
class UserProfile:
    """Thông tin hồ sơ cá nhân của người học."""
    # Định danh (ID)
    user_id: str = ""                 # ID định danh hệ thống (Trùng khớp auth id)
    
    # Thông tin cơ bản từ Auth
    email: str = ""                  # Email đăng ký
    display_name: str = ""           # Tên hiển thị người dùng chọn
    
    # Quá trình học tập
    current_level: ProficiencyLevel = ProficiencyLevel.A1 # Trình độ hiện tại
    learning_goal: ProficiencyLevel        # Mục tiêu học tập 
    role: Role = Role.LEARNER        # Vai trò trong hệ thống
    is_active: bool = True           # Trạng thái tài khoản
    current_streak: int = 0          # Số ngày học liên tục (Chuỗi streak)
    last_completed_at: str = ""      # Thời điểm hoàn thành bài học cuối (ISO string)
    total_words_learned: int = 0     # Tổng số từ vựng đã học được

    def __post_init__(self):
        # Kiểm tra tính toàn vẹn dữ liệu bắt buộc
        if not self.user_id:
            raise ValueError("user_id là bắt buộc để khởi tạo UserProfile")

    def update_streak(self):
        """Logic tăng chuỗi ngày học."""
        self.current_streak += 1
        
    def add_learned_word(self, count: int = 1):
        """Cập nhật kho từ vựng cá nhân."""
        self.total_words_learned += count

    def update_level(self, new_level: ProficiencyLevel):
        """Nâng cấp trình độ của người dùng."""
        self.current_level = new_level

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UserProfile):
            return False
        return self.user_id == other.user_id

    def __hash__(self) -> int:
        return hash(self.user_id)
