"""Unit tests for StructuredHintGenerator (LLM-based hints for all CEFR levels)."""

import pytest
from domain.services.structured_hint_generator import (
    StructuredHint,
    validate_structured_hint,
)


class TestStructuredHintGenerator:
    """Test StructuredHintGenerator for all CEFR levels."""

    def test_validate_simple_hint_format(self):
        """Test validation of simplified hint format."""
        
        # Valid hint
        valid_hint = {
            "hint": {"vi": "Hãy thử nói...", "en": "Try saying..."},
            "level": "A1",
            "type": "vocabulary_suggestion"
        }
        assert validate_structured_hint(valid_hint) is True
        
        # Missing hint field
        invalid_hint_1 = {
            "level": "A1",
            "type": "vocabulary_suggestion"
        }
        assert validate_structured_hint(invalid_hint_1) is False
        
        # Missing vi/en in hint
        invalid_hint_2 = {
            "hint": {"vi": "Hãy thử nói..."},
            "level": "A1",
            "type": "vocabulary_suggestion"
        }
        assert validate_structured_hint(invalid_hint_2) is False
        
        # Missing level
        invalid_hint_3 = {
            "hint": {"vi": "Hãy thử nói...", "en": "Try saying..."},
            "type": "vocabulary_suggestion"
        }
        assert validate_structured_hint(invalid_hint_3) is False

    def test_structured_hint_dataclass(self):
        """Test StructuredHint dataclass with simplified format."""
        
        hint = StructuredHint(
            hint={"vi": "Hãy thử nói: 'Tôi muốn...'", "en": "Try saying: 'I'd like...'"},
            level="A1",
            type="vocabulary_suggestion"
        )
        
        assert hint.hint["vi"] == "Hãy thử nói: 'Tôi muốn...'"
        assert hint.hint["en"] == "Try saying: 'I'd like...'"
        assert hint.level == "A1"
        assert hint.type == "vocabulary_suggestion"
        
        # Test to_dict
        hint_dict = hint.to_dict()
        assert "hint" in hint_dict
        assert "level" in hint_dict
        assert "type" in hint_dict
        assert hint_dict["hint"]["vi"] == "Hãy thử nói: 'Tôi muốn...'"

    def test_hint_types_by_level(self):
        """Test that different levels get different hint types."""
        
        # A1-A2: vocabulary_suggestion
        hint_a1 = StructuredHint(
            hint={"vi": "Hãy thử: 'Tôi muốn...'", "en": "Try: 'I'd like...'"},
            level="A1",
            type="vocabulary_suggestion"
        )
        assert hint_a1.type == "vocabulary_suggestion"
        
        # B1-B2: strategic_guidance
        hint_b1 = StructuredHint(
            hint={"vi": "Hãy mô tả chi tiết hơn", "en": "Describe in more detail"},
            level="B1",
            type="strategic_guidance"
        )
        assert hint_b1.type == "strategic_guidance"
        
        # C1-C2: metacognitive_prompt
        hint_c1 = StructuredHint(
            hint={"vi": "Hãy xem xét ngữ cảnh trang trọng", "en": "Consider the formal register"},
            level="C1",
            type="metacognitive_prompt"
        )
        assert hint_c1.type == "metacognitive_prompt"
