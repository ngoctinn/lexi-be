from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from ulid import ULID

from domain.value_objects.enums import Speaker

@dataclass
class Turn:
    """Một lượt thoại đơn lẻ trong nội dung hội thoại."""

    # Liên kết và vị trí
    session_id: ULID            # ID của session chứa lượt thoại này
    turn_index: int = 0             # Thứ tự lượt nói trong session (0, 1, 2...)
    
    # Nội dung và Metadata
    speaker: Speaker = Speaker.AI   # Vai trò người nói (AI/USER)
    content: str = ""                # Nội dung văn bản của lượt thoại
    audio_url: str = ""              # Đường dẫn file âm thanh (nếu có)
    translated_content: str = ""      # Bản dịch của nội dung (thường là sang tiếng Việt)
    is_hint_used: bool = False       # Lượt này có phải là kết quả của một gợi ý không
    
    # Phase 5: Performance Metrics
    ttft_ms: Optional[Decimal] = None            # Time to first token (milliseconds)
    latency_ms: Optional[Decimal] = None         # Total latency (milliseconds)
    input_tokens: int = 0                        # Input tokens used
    output_tokens: int = 0                       # Output tokens generated
    cost_usd: Decimal = Decimal("0.0")           # Cost for this turn
    delivery_cue: str = ""                       # Delivery cue used (e.g., "[warmly]")

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
        return self.session_id == other.session_id and self.turn_index == other.turn_index

    def __hash__(self) -> int:
        return hash((self.session_id, self.turn_index))
