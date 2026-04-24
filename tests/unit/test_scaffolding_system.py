"""Unit tests for ScaffoldingSystem."""

import pytest
from domain.services.scaffolding_system import (
    ScaffoldingSystem,
    HintLevel,
    SilenceThreshold,
    BilingualHint,
)


class TestScaffoldingSystem:
    """Test ScaffoldingSystem bilingual hints."""

    def test_scaffolding_initialization(self):
        """Test ScaffoldingSystem initialization."""
        system = ScaffoldingSystem(enable_scaffolding=True)
        assert system.enable_scaffolding is True
        assert system.hint_count == 0

    def test_scaffolding_disabled(self):
        """Test ScaffoldingSystem with scaffolding disabled."""
        system = ScaffoldingSystem(enable_scaffolding=False)
        assert system.enable_scaffolding is False

    def test_should_provide_hint_a1_10s(self):
        """Test hint should be provided for A1 at 10s silence."""
        system = ScaffoldingSystem()
        assert system.should_provide_hint(10, "A1") is True

    def test_should_provide_hint_a1_20s(self):
        """Test hint should be provided for A1 at 20s silence."""
        system = ScaffoldingSystem()
        assert system.should_provide_hint(20, "A1") is True

    def test_should_provide_hint_a1_30s(self):
        """Test hint should be provided for A1 at 30s silence."""
        system = ScaffoldingSystem()
        assert system.should_provide_hint(30, "A1") is True

    def test_should_provide_hint_a2_10s(self):
        """Test hint should be provided for A2 at 10s silence."""
        system = ScaffoldingSystem()
        assert system.should_provide_hint(10, "A2") is True

    def test_should_provide_hint_b1_no_hint(self):
        """Test no hint for B1 level."""
        system = ScaffoldingSystem()
        assert system.should_provide_hint(10, "B1") is False

    def test_should_provide_hint_disabled(self):
        """Test no hint when scaffolding disabled."""
        system = ScaffoldingSystem(enable_scaffolding=False)
        assert system.should_provide_hint(10, "A1") is False

    def test_should_provide_hint_wrong_duration(self):
        """Test no hint at wrong silence duration."""
        system = ScaffoldingSystem()
        assert system.should_provide_hint(5, "A1") is False
        assert system.should_provide_hint(15, "A1") is False
        assert system.should_provide_hint(25, "A1") is False

    def test_get_hint_level_10s(self):
        """Test hint level at 10s is GENTLE_PROMPT."""
        system = ScaffoldingSystem()
        hint_level = system.get_hint_level(10)
        assert hint_level == HintLevel.GENTLE_PROMPT

    def test_get_hint_level_20s(self):
        """Test hint level at 20s is VOCABULARY_HINT."""
        system = ScaffoldingSystem()
        hint_level = system.get_hint_level(20)
        assert hint_level == HintLevel.VOCABULARY_HINT

    def test_get_hint_level_30s(self):
        """Test hint level at 30s is SENTENCE_STARTER."""
        system = ScaffoldingSystem()
        hint_level = system.get_hint_level(30)
        assert hint_level == HintLevel.SENTENCE_STARTER

    def test_get_hint_level_invalid(self):
        """Test hint level for invalid duration."""
        system = ScaffoldingSystem()
        hint_level = system.get_hint_level(15)
        assert hint_level is None

    def test_generate_hint_a1_gentle_prompt(self):
        """Test generating gentle prompt for A1."""
        system = ScaffoldingSystem()
        hint = system.generate_hint("A1", 10)
        
        assert hint is not None
        assert hint.hint_level == HintLevel.GENTLE_PROMPT
        assert hint.silence_duration_seconds == 10
        assert "Hãy tiếp tục" in hint.vietnamese
        assert "Keep going" in hint.english

    def test_generate_hint_a1_vocabulary_hint(self):
        """Test generating vocabulary hint for A1."""
        system = ScaffoldingSystem()
        hint = system.generate_hint("A1", 20)
        
        assert hint is not None
        assert hint.hint_level == HintLevel.VOCABULARY_HINT
        assert hint.silence_duration_seconds == 20
        assert "từ" in hint.vietnamese
        assert "word" in hint.english

    def test_generate_hint_a1_sentence_starter(self):
        """Test generating sentence starter for A1."""
        system = ScaffoldingSystem()
        hint = system.generate_hint("A1", 30)
        
        assert hint is not None
        assert hint.hint_level == HintLevel.SENTENCE_STARTER
        assert hint.silence_duration_seconds == 30
        assert "I like" in hint.english

    def test_generate_hint_a2_gentle_prompt(self):
        """Test generating gentle prompt for A2."""
        system = ScaffoldingSystem()
        hint = system.generate_hint("A2", 10)
        
        assert hint is not None
        assert hint.hint_level == HintLevel.GENTLE_PROMPT
        assert "Hãy tiếp tục" in hint.vietnamese

    def test_generate_hint_b1_no_hint(self):
        """Test no hint for B1 level."""
        system = ScaffoldingSystem()
        hint = system.generate_hint("B1", 10)
        assert hint is None

    def test_generate_hint_disabled(self):
        """Test no hint when scaffolding disabled."""
        system = ScaffoldingSystem(enable_scaffolding=False)
        hint = system.generate_hint("A1", 10)
        assert hint is None

    def test_generate_hint_with_context(self):
        """Test generating hint with context."""
        system = ScaffoldingSystem()
        context = {
            "word": "restaurant",
            "example": "I like the restaurant",
            "meaning": "a place to eat",
        }
        hint = system.generate_hint("A1", 20, context)
        
        assert hint is not None
        assert "restaurant" in hint.vietnamese
        assert "restaurant" in hint.english

    def test_format_hint_for_display(self):
        """Test formatting hint for display."""
        system = ScaffoldingSystem()
        hint = system.generate_hint("A1", 10)
        
        formatted = system.format_hint_for_display(hint)
        
        # Should have Vietnamese first, then English
        assert hint.vietnamese in formatted
        assert hint.english in formatted
        assert formatted.index(hint.vietnamese) < formatted.index(hint.english)

    def test_hint_count_increments(self):
        """Test hint count increments."""
        system = ScaffoldingSystem()
        assert system.get_hint_count() == 0
        
        system.generate_hint("A1", 10)
        assert system.get_hint_count() == 1
        
        system.generate_hint("A1", 20)
        assert system.get_hint_count() == 2

    def test_hint_count_no_increment_when_no_hint(self):
        """Test hint count doesn't increment when no hint provided."""
        system = ScaffoldingSystem()
        system.generate_hint("B1", 10)  # No hint for B1
        assert system.get_hint_count() == 0

    def test_reset_hint_count(self):
        """Test resetting hint count."""
        system = ScaffoldingSystem()
        system.generate_hint("A1", 10)
        system.generate_hint("A1", 20)
        assert system.get_hint_count() == 2
        
        system.reset_hint_count()
        assert system.get_hint_count() == 0

    def test_is_scaffolding_enabled(self):
        """Test checking if scaffolding is enabled."""
        system1 = ScaffoldingSystem(enable_scaffolding=True)
        assert system1.is_scaffolding_enabled() is True
        
        system2 = ScaffoldingSystem(enable_scaffolding=False)
        assert system2.is_scaffolding_enabled() is False

    def test_bilingual_hint_structure(self):
        """Test BilingualHint structure."""
        hint = BilingualHint(
            vietnamese="Tiếng Việt",
            english="English",
            hint_level=HintLevel.GENTLE_PROMPT,
            silence_duration_seconds=10,
        )
        
        assert hint.vietnamese == "Tiếng Việt"
        assert hint.english == "English"
        assert hint.hint_level == HintLevel.GENTLE_PROMPT
        assert hint.silence_duration_seconds == 10

    def test_hint_level_enum(self):
        """Test HintLevel enum values."""
        assert HintLevel.GENTLE_PROMPT.value == "gentle_prompt"
        assert HintLevel.VOCABULARY_HINT.value == "vocabulary_hint"
        assert HintLevel.SENTENCE_STARTER.value == "sentence_starter"

    def test_silence_threshold_enum(self):
        """Test SilenceThreshold enum values."""
        assert SilenceThreshold.FIRST.value == 10
        assert SilenceThreshold.SECOND.value == 20
        assert SilenceThreshold.THIRD.value == 30

    def test_multiple_hints_sequence(self):
        """Test generating multiple hints in sequence."""
        system = ScaffoldingSystem()
        
        # First hint at 10s
        hint1 = system.generate_hint("A1", 10)
        assert hint1.hint_level == HintLevel.GENTLE_PROMPT
        
        # Second hint at 20s
        hint2 = system.generate_hint("A1", 20)
        assert hint2.hint_level == HintLevel.VOCABULARY_HINT
        
        # Third hint at 30s
        hint3 = system.generate_hint("A1", 30)
        assert hint3.hint_level == HintLevel.SENTENCE_STARTER
        
        # Total hints should be 3
        assert system.get_hint_count() == 3

    def test_vietnamese_first_in_display(self):
        """Test Vietnamese appears first in display format."""
        system = ScaffoldingSystem()
        hint = system.generate_hint("A1", 10)
        formatted = system.format_hint_for_display(hint)
        
        # Find positions
        viet_pos = formatted.find(hint.vietnamese)
        eng_pos = formatted.find(hint.english)
        
        # Vietnamese should come first
        assert viet_pos < eng_pos
        assert viet_pos == 0  # Should be at the beginning
