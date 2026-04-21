from dataclasses import dataclass
from typing import Optional

from domain.value_objects.enums import VocabType

@dataclass
class Vocabulary:
    """Thông tin từ vựng trong từ điển hệ thống."""
    # Dữ liệu từ vựng
    word: str = ""                   # Từ vựng (Viết thường, đã trim)
    word_type: VocabType = VocabType.NOUN            # Loại từ (n, v, adj...)
    translation_vi: str = ""         # Bản dịch tiếng Việt của từ gốc
    definition_vi: str = ""          # Định nghĩa / giải nghĩa tiếng Việt
    phonetic: str = ""               # Cách phát âm (IPA)
    audio_url: str = ""              # Đường dẫn file phát âm
    example_sentence: str = ""       # Câu ví dụ mẫu

    # Thông tin nguồn
    source_api: Optional[str] = ""    # Tên API nguồn lấy dữ liệu

    def __post_init__(self):
        if not self.word:
            raise ValueError("word không được để trống trong Vocabulary")
        # Chuẩn hóa dữ liệu để dùng làm ID đồng nhất
        self.word = self.word.strip().lower()

    def format_entry(self) -> str:
        """Định dạng nhanh thông tin hiển thị."""
        parts = [part for part in [self.translation_vi, self.definition_vi] if part]
        if not parts:
            return f"{self.word} ({self.word_type})"
        return f"{self.word} ({self.word_type}): {' | '.join(parts)}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vocabulary):
            return False
        return self.word == other.word

    def __hash__(self) -> int:
        return hash(self.word)
