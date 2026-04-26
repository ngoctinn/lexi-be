from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

@dataclass
class FlashCard:
    """
    Thực thể FlashCard đại diện cho một thẻ từ vựng cá nhân của người học.
    
    Tích hợp thuật toán lặp lại ngắt quãng (SRS) cơ bản để tối ưu việc ghi nhớ.
    """
    # Định danh
    flashcard_id: str                      # ULID định danh duy nhất cho thẻ
    user_id: str                           # ID người dùng sở hữu thẻ
    word: str                             # Từ vựng liên kết

    # Nội dung học
    translation_vi: str = ""               # Bản dịch ngắn gọn (mặt sau - dòng 1)
    phonetic: str = ""                     # Phiên âm (mặt sau - dòng 3)
    audio_url: str = ""                    # URL audio phát âm (mặt sau - link)
    example_sentence: str = ""             # Câu ví dụ (mặt sau - dòng 2)

    # Dữ liệu SRS (Spaced Repetition System)
    review_count: int = 0                  # Số lần đã ôn tập
    interval_days: int = 1                 # Khoảng cách ngày ôn tiếp theo
    difficulty: int = 0                    # Mức độ khó (0-5)
    last_reviewed_at: Optional[datetime] = None
    next_review_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Source tracking (từ session)
    source_session_id: Optional[str] = None
    source_turn_index: Optional[int] = None

    def __post_init__(self):
        # 1. Kiểm tra tính toàn vẹn (Validation)
        if not self.flashcard_id or not self.user_id or not self.word:
            raise ValueError("flashcard_id, user_id và word là thông tin bắt buộc.")
            
        if not (0 <= self.difficulty <= 5):
            raise ValueError(f"Độ khó phải nằm trong khoảng 0-5. Nhận được: {self.difficulty}")

    def update_srs(self, rating: int):
        """
        Cập nhật logic SRS dựa trên phản hồi của người dùng.
        Logic SM-2 rút gọn.
        """
        now = datetime.now(timezone.utc)
        self.last_reviewed_at = now
        self.review_count += 1
        
        # Logic tính toán khoảng cách ôn tập tiếp theo (Simplified SRS)
        if rating >= 3:
            # Nếu người dùng nhớ tốt, tăng khoảng cách (tối đa 365 ngày)
            self.interval_days = min(self.interval_days * 2, 365)
        else:
            # Nếu quên, reset lại chu kỳ từ đầu
            self.interval_days = 1
            
        self.next_review_at = now + timedelta(days=self.interval_days)

    def apply_review(self, rating: str) -> None:
        """
        Cập nhật SRS dựa trên đánh giá của người dùng (string rating).
        
        rating: "forgot" | "hard" | "good" | "easy"
        """
        VALID_RATINGS = {"forgot", "hard", "good", "easy"}
        if rating not in VALID_RATINGS:
            raise ValueError(f"Rating không hợp lệ '{rating}'. Phải là một trong: {VALID_RATINGS}")

        now = datetime.now(timezone.utc)
        # Cast sang int để tránh lỗi Decimal * float khi đọc từ DynamoDB
        old_interval = int(self.interval_days)

        if rating == "forgot":
            new_interval = 1
        elif rating == "hard":
            new_interval = max(1, round(old_interval * 1.2))
        elif rating == "good":
            new_interval = round(old_interval * 2.5)
        else:  # easy
            new_interval = round(old_interval * 3.0)

        self.interval_days = new_interval
        self.last_reviewed_at = now
        self.next_review_at = now + timedelta(days=new_interval)
        self.review_count += 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FlashCard):
            return False
        return self.flashcard_id == other.flashcard_id

    def __hash__(self) -> int:
        return hash(self.flashcard_id)
