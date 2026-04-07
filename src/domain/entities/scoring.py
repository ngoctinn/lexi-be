from dataclasses import dataclass
from ulid import ULID

@dataclass
class Scoring:
    """Kết quả chấm điểm hội thoại của một phiên học."""
    # Định danh (ID)
    scoring_id: ULID # ID bản ghi chấm điểm
    
    # Liên kết
    session_id: ULID             # ID của session hội thoại tương ứng
    
    # Chi tiết điểm số (0-100)
    grammar_score: int = 0           # Điểm ngữ pháp
    vocabulary_score: int = 0        # Điểm phong phú từ vựng
    fluency_score: int = 0           # Điểm độ trôi chảy
    coherence_score: int = 0       # Điểm tính mạch lạc
    overall_score: int = 0           # Điểm tổng kết
    feedback_fluency: str = ""       # Nhận xét chi tiết từ AI

    def __post_init__(self):
        # Kiểm tra session_id
        if not self.session_id:
            raise ValueError("Scoring phải liên kết với một session_id")
            
        # Kiểm tra dải điểm
        scores = [self.grammar_score, self.vocabulary_score, self.fluency_score, self.coherence_score]
        for score in scores:
            if not (0 <= score <= 100):
                raise ValueError(f"Điểm số phải từ 0-100, nhận được {score}")
        
    def calculate_overall(self):
        """Tự động tính điểm trung bình tổng quát."""
        scores = [self.grammar_score, self.vocabulary_score, self.fluency_score, self.coherence_score]
        self.overall_score = round(sum(scores) / len(scores))
        
    def add_feedback(self, feedback: str):
        """Cập nhật nội dung nhận xét."""
        self.feedback_fluency = feedback

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Scoring):
            return False
        return self.scoring_id == other.scoring_id

    def __hash__(self) -> int:
        return hash(self.scoring_id)
