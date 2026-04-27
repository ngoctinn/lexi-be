from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.domain.services.srs_engine import SRSEngine

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
    difficulty: int = 0                    # Mức độ khó (0-5) - legacy field
    ease_factor: float = 2.5               # SM-2 ease factor (1.3-2.5)
    repetition_count: int = 0              # SM-2 consecutive successful reviews
    last_reviewed_at: Optional[datetime] = None
    next_review_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Source tracking (từ session)
    source_session_id: Optional[str] = None
    source_turn_index: Optional[int] = None

    def __post_init__(self):
        # 1. Kiểm tra tính toàn vẹn (Validation)
        if not self.flashcard_id or not self.user_id:
            raise ValueError("flashcard_id và user_id là thông tin bắt buộc.")
        
        # Trim and validate word
        self.word = self.word.strip() if self.word else ""
        
        if not self.word:
            raise ValueError("word là thông tin bắt buộc và không được chỉ chứa khoảng trắng.")
        
        if len(self.word) > 100:
            raise ValueError(f"Từ không được vượt quá 100 ký tự. Nhận được: {len(self.word)} ký tự")
        
        # Validate word contains only allowed characters (letters, spaces, hyphens, apostrophes)
        # Allow: a-z, A-Z, 0-9, spaces, hyphens, apostrophes, forward slashes
        import re
        if not re.match(r"^[a-zA-Z0-9\s\-'/]+$", self.word):
            raise ValueError(f"Từ chỉ được chứa chữ cái, số, khoảng trắng, dấu gạch ngang, dấu ngoặc kép, và dấu gạch chéo. Nhận được: {self.word}")
            
        if not (0 <= self.difficulty <= 5):
            raise ValueError(f"Độ khó phải nằm trong khoảng 0-5. Nhận được: {self.difficulty}")
        
        # Validate SM-2 fields
        if not (1.3 <= self.ease_factor <= 2.5):
            raise ValueError(f"Ease factor phải nằm trong khoảng 1.3-2.5. Nhận được: {self.ease_factor}")
        
        if self.repetition_count < 0:
            raise ValueError(f"Repetition count phải >= 0. Nhận được: {self.repetition_count}")

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

    def apply_sm2_review(self, rating: str) -> None:
        """
        Apply SM-2 algorithm based on user rating.
        
        Args:
            rating: String rating ("forgot", "hard", "good", "easy")
        
        Updates:
            - ease_factor: SM-2 ease factor
            - repetition_count: Consecutive successful reviews
            - interval_days: Days until next review
            - next_review_at: Timestamp of next review
            - review_count: Total review count (for statistics)
        """
        quality = SRSEngine.map_rating_to_quality(rating)
        
        new_interval, new_repetition_count, new_ease_factor = SRSEngine.calculate_next_interval(
            quality=quality,
            repetition_count=self.repetition_count,
            ease_factor=self.ease_factor,
            previous_interval=self.interval_days
        )
        
        self.interval_days = new_interval
        self.repetition_count = new_repetition_count
        self.ease_factor = new_ease_factor
        self.last_reviewed_at = datetime.now(timezone.utc)
        self.next_review_at = self.last_reviewed_at + timedelta(days=new_interval)
        self.review_count += 1

    def apply_sm2_review(self, rating: str) -> None:
        """
        Apply SM-2 algorithm based on user rating.
        
        Args:
            rating: String rating ("forgot", "hard", "good", "easy")
        
        Updates:
            - ease_factor: SM-2 ease factor
            - repetition_count: Consecutive successful reviews
            - interval_days: Days until next review
            - next_review_at: Timestamp of next review
            - review_count: Total review count (for statistics)
        """
        quality = SRSEngine.map_rating_to_quality(rating)
        
        new_interval, new_repetition_count, new_ease_factor = SRSEngine.calculate_next_interval(
            quality=quality,
            repetition_count=self.repetition_count,
            ease_factor=self.ease_factor,
            previous_interval=self.interval_days
        )
        
        self.interval_days = new_interval
        self.repetition_count = new_repetition_count
        self.ease_factor = new_ease_factor
        self.last_reviewed_at = datetime.now(timezone.utc)
        self.next_review_at = self.last_reviewed_at + timedelta(days=new_interval)
        self.review_count += 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FlashCard):
            return False
        return self.flashcard_id == other.flashcard_id

    def __hash__(self) -> int:
        return hash(self.flashcard_id)
