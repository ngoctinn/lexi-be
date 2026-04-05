from dataclasses import dataclass, field
from typing import Optional
from ulid import ULID

@dataclass
class WordCache:
    """Dữ liệu đệm từ vựng để tối ưu hiệu năng và chi phí API."""
    # Định danh (ID)
    word_id: str = field(default_factory=lambda: str(ULID()), init=False) # ID bản ghi cache
    
    # Dữ liệu từ vựng
    word: str = ""                   # Từ vựng (Viết thường, đã trim)
    word_type: str = ""              # Loại từ (n, v, adj...)
    definition_vi: str = ""          # Định nghĩa nghĩa tiếng Việt
    phonetic: str = ""               # Cách phát âm (IPA)
    audio_s3_key: str = ""           # Đường dẫn file phát âm trên S3
    example_sentence: str = ""       # Câu ví dụ mẫu
    
    # Thông tin nguồn
    source_api: Optional[str] = ""    # Tên API nguồn lấy dữ liệu

    def __post_init__(self):
        if not self.word:
            raise ValueError("word không được để trống trong WordCache")
        # Chuẩn hóa dữ liệu
        self.word = self.word.strip().lower()

    def format_entry(self) -> str:
        """Định dạng nhanh thông tin hiển thị."""
        return f"{self.word} ({self.word_type}): {self.definition_vi}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WordCache):
            return False
        return self.word_cache_id == other.word_cache_id

    def __hash__(self) -> int:
        return hash(self.word_cache_id)
