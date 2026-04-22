from dataclasses import dataclass, field
from typing import Dict, List, Optional

from domain.value_objects.enums import VocabType

@dataclass
class Vocabulary:
    """Thông tin từ vựng trong từ điển hệ thống."""
    word: str = ""
    word_type: VocabType = VocabType.NOUN
    translation_vi: str = ""
    definition_vi: str = ""
    phonetic: str = ""
    audio_url: str = ""
    example_sentence: str = ""
    source_api: Optional[str] = ""
    all_meanings: List[Dict[str, str]] = field(default_factory=list)  # [{part_of_speech, definition_vi, example_sentence}]

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
