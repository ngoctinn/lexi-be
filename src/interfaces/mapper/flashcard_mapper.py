from typing import Any, Dict

from application.dtos.flashcard_dtos import CreateFlashCardCommand


class FlashCardMapper:
    """Phiên dịch dữ liệu HTTP sang command của application."""

    @staticmethod
    def to_create_command(body: Dict[str, Any], user_id: str) -> CreateFlashCardCommand:
        """
        Chuyển đổi request body thành CreateFlashCardCommand.
        
        Expected body:
        {
            "vocab": "word or phrase",
            "vocab_type": "noun|verb|adj|...",
            "translation_vi": "Nghĩa tiếng Việt",
            "phonetic": "Phiên âm (optional)",
            "audio_url": "URL audio (optional)",
            "example_sentence": "Câu ví dụ (optional)",
            "source_api": "Nguồn API (optional)",
            "source_session_id": "Session ID (optional)",
            "source_turn_index": "Turn index (optional)"
        }
        """
        return CreateFlashCardCommand(
            user_id=user_id,
            vocab=body.get("vocab", ""),
            vocab_type=body.get("vocab_type", "noun"),
            translation_vi=body.get("translation_vi", ""),
            phonetic=body.get("phonetic", ""),
            audio_url=body.get("audio_url", ""),
            example_sentence=body.get("example_sentence", ""),
            source_api=body.get("source_api", "internal"),
            source_session_id=body.get("source_session_id"),
            source_turn_index=body.get("source_turn_index"),
        )
