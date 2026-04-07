from dataclasses import dataclass
from ulid import ULID

from domain.value_objects.enums import Speaker

@dataclass
class Turn:
    """Một lượt thoại đơn lẻ trong nội dung hội thoại."""

    # Liên kết và vị trí
    session_id: ULID            # ID của session chứa lượt thoại này
    turn_index: int = 0              # Thứ tự lượt nói trong session (0, 1, 2...)
    
    # Nội dung và Metadata
    speaker: Speaker = Speaker.AI   # Vai trò người nói (AI/USER)
    content: str = ""                # Nội dung văn bản của lượt thoại
    audio_url: str = ""              # Đường dẫn file âm thanh (nếu có)
    translated_content: str = ""      # Bản dịch của nội dung (thường là sang tiếng Việt)
    is_hint_used: bool = False       # Lượt này có phải là kết quả của một gợi ý không

    def __post_init__(self):
        if not self.session_id:
            raise ValueError("Mỗi lượt thoại phải thuộc về một session_id")

    def set_content(self, text: str, audio_url: str = ""):
        """Thiết lập văn bản và audio của lượt nói."""
        self.content = text
        if audio_url:
            self.audio_url = audio_url
        
    def add_translation(self, text: str):
        """Gán nội dung dịch thuật."""
        self.translated_content = text
            
    def mark_hint_used(self):
        """Ghi nhận lượt này user đã dùng gợi ý."""
        self.is_hint_used = True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Turn):
            return False
        return self.turn_id == other.turn_id

    def __hash__(self) -> int:
        return hash(self.turn_id)
