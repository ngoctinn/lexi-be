from dataclasses import dataclass
from ulid import ULID

@dataclass
class Scenario:
    """Kịch bản hội thoại mẫu do hệ thống biên soạn."""
    # Định danh (ID)
    scenario_id: ULID # ID duy nhất của kịch bản
    
    # Nội dung kịch bản
    scenario_title: str = ""         # Tiêu đề hiển thị cho người dùng
    scenario_prompt: str = ""        # Lệnh điều hướng (Prompt) cho AI
    my_character: str = ""           # Nhân vật người dùng sẽ đóng vai
    ai_character: str = ""           # Nhân vật AI sẽ đóng vai
    
    # Trạng thái
    is_active: bool = True           # Kịch bản có đang được sử dụng hay không

    def __post_init__(self):
        # Kiểm tra tính toàn vẹn dữ liệu bắt buộc
        if not self.scenario_title or not self.scenario_prompt:
            raise ValueError("scenario_title và scenario_prompt không được để trống")

    def increment_usage(self):
        """Tăng bộ đếm lượt sử dụng."""
        self.usage_count += 1

    def deactivate(self):
        """Ngừng kích hoạt kịch bản."""
        self.is_active = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Scenario):
            return False
        return self.scenario_id == other.scenario_id

    def __hash__(self) -> int:
        return hash(self.scenario_id)
