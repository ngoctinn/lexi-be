from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class CreateFlashCardCommand:
    user_id: str
    vocab: str
    vocab_type: str = ""              # Loại từ (n, v, adj...)
    definition_vi: str = ""          # Định nghĩa nghĩa tiếng Việt
    phonetic: str = ""               # Cách phát âm (IPA)
    audio_url: str = ""              # Đường dẫn file phát âm 
    example_sentence: str = ""       # Câu ví dụ mẫu
    
    # Thông tin nguồn
    source_api: Optional[str] = "" 
