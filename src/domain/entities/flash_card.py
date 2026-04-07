from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from ulid import ULID

@dataclass
class FlashCard:
    # Định danh (ID)
    flashcard_id: ULID # ID duy nhất của thẻ
    
    # Thông tin cơ bản
    user_id: str = ""                # ID của người dùng sở hữu thẻ (Trùng khớp auth id)
    vocabulary: str = ""          # ID của từ vựng (Liên kết với Vocabulary entity)
    
    # Trạng thái ghi nhớ (SRS)
    review_count: int = 0            # Số lần đã thực hiện ôn tập
    interval_days: int = 1           # Khoảng cách ngày cho lần ôn tiếp theo
    difficulty: int = 0              # Mức độ khó (0-5)
    last_reviewed_at: str = datetime.now(timezone.utc).isoformat() # Thời điểm vừa ôn tập xong (ISO string)
    next_review_at: str = datetime.now(timezone.utc).isoformat() # Thời điểm cần ôn tập tiếp

    def __post_init__(self):
        # Kiểm tra tính toàn vẹn dữ liệu bắt buộc
        if not self.user_id or not self.vocabulary_id:
            raise ValueError("user_id và vocabulary_id là bắt buộc cho FlashCard")
        if not (0 <= self.difficulty <= 5):
            raise ValueError(f"Độ khó phải từ 0-5, nhận được {self.difficulty}")

    def update_srs(self, rating: int):
        """Cập nhật dữ liệu lặp lại ngắt quãng dựa trên đánh giá của người dùng."""
        now = datetime.now(timezone.utc)
        self.last_reviewed_at = now.isoformat()
        self.review_count += 1
        
        if rating >= 3:
            self.interval_days = min(self.interval_days * 2, 365)
        else:
            self.interval_days = 1
            
        next_review_date = now + timedelta(days=self.interval_days)
        self.next_review_at = next_review_date.isoformat()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FlashCard):
            return False
        return self.flashcard_id == other.flashcard_id

    def __hash__(self) -> int:
        return hash(self.flashcard_id)
