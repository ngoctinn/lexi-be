"""Bilingual Scaffolding System for A1-A2 learners."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class HintLevel(Enum):
    """Hint levels for scaffolding."""
    GENTLE_PROMPT = "gentle_prompt"  # Encourage to continue
    VOCABULARY_HINT = "vocabulary_hint"  # Suggest vocabulary
    SENTENCE_STARTER = "sentence_starter"  # Provide sentence starter


class SilenceThreshold(Enum):
    """Silence detection thresholds (in seconds)."""
    FIRST = 10  # First hint at 10s
    SECOND = 20  # Second hint at 20s
    THIRD = 30  # Third hint at 30s


@dataclass
class BilingualHint:
    """Bilingual hint with Vietnamese and English."""
    vietnamese: str
    english: str
    hint_level: HintLevel
    silence_duration_seconds: int


class ScaffoldingSystem:
    """Generates bilingual hints for A1-A2 learners."""

    # Hint templates per level
    _GENTLE_PROMPTS = {
        "A1": {
            "vietnamese": "Hãy tiếp tục nói! Bạn đang làm rất tốt.",
            "english": "Keep going! You're doing great.",
        },
        "A2": {
            "vietnamese": "Hãy tiếp tục! Bạn có thể nói thêm được.",
            "english": "Keep going! You can say more.",
        },
    }

    _VOCABULARY_HINTS = {
        "A1": {
            "vietnamese": "Bạn có thể dùng từ: [word]. Ví dụ: [example]",
            "english": "You can use the word: [word]. Example: [example]",
        },
        "A2": {
            "vietnamese": "Hãy thử dùng từ: [word]. Nó có nghĩa là: [meaning]",
            "english": "Try using the word: [word]. It means: [meaning]",
        },
    }

    _SENTENCE_STARTERS = {
        "A1": {
            "vietnamese": "Bạn có thể bắt đầu bằng: 'I like...' hoặc 'I have...'",
            "english": "You can start with: 'I like...' or 'I have...'",
        },
        "A2": {
            "vietnamese": "Hãy bắt đầu bằng: 'I think...' hoặc 'I believe...'",
            "english": "Start with: 'I think...' or 'I believe...'",
        },
    }

    def __init__(self, enable_scaffolding: bool = True):
        """Initialize scaffolding system.
        
        Args:
            enable_scaffolding: Whether to enable scaffolding hints
        """
        self.enable_scaffolding = enable_scaffolding
        self.hint_count = 0  # Track number of hints given

    def should_provide_hint(
        self,
        silence_duration_seconds: int,
        proficiency_level: str,
    ) -> bool:
        """Determine if hint should be provided based on silence duration.
        
        Args:
            silence_duration_seconds: Duration of silence in seconds
            proficiency_level: Proficiency level (A1, A2, B1, etc.)
            
        Returns:
            True if hint should be provided, False otherwise
        """
        if not self.enable_scaffolding:
            return False

        # Only provide hints for A1-A2
        if proficiency_level not in ["A1", "A2"]:
            return False

        # Provide hints at 10s, 20s, 30s
        if silence_duration_seconds in [10, 20, 30]:
            return True

        return False

    def get_hint_level(self, silence_duration_seconds: int) -> Optional[HintLevel]:
        """Get hint level based on silence duration.
        
        Args:
            silence_duration_seconds: Duration of silence in seconds
            
        Returns:
            HintLevel or None if no hint should be provided
        """
        if silence_duration_seconds == 10:
            return HintLevel.GENTLE_PROMPT
        elif silence_duration_seconds == 20:
            return HintLevel.VOCABULARY_HINT
        elif silence_duration_seconds == 30:
            return HintLevel.SENTENCE_STARTER
        return None

    def generate_hint(
        self,
        proficiency_level: str,
        silence_duration_seconds: int,
        context: Optional[dict] = None,
    ) -> Optional[BilingualHint]:
        """Generate bilingual hint for learner.
        
        Args:
            proficiency_level: Proficiency level (A1, A2)
            silence_duration_seconds: Duration of silence in seconds
            context: Optional context (vocabulary, scenario, etc.)
            
        Returns:
            BilingualHint or None if no hint should be provided
        """
        if not self.should_provide_hint(silence_duration_seconds, proficiency_level):
            return None

        hint_level = self.get_hint_level(silence_duration_seconds)
        if not hint_level:
            return None

        # Generate hint based on level
        if hint_level == HintLevel.GENTLE_PROMPT:
            template = self._GENTLE_PROMPTS.get(proficiency_level)
        elif hint_level == HintLevel.VOCABULARY_HINT:
            template = self._VOCABULARY_HINTS.get(proficiency_level)
        elif hint_level == HintLevel.SENTENCE_STARTER:
            template = self._SENTENCE_STARTERS.get(proficiency_level)
        else:
            return None

        if not template:
            return None

        # Replace placeholders if context provided
        vietnamese = template["vietnamese"]
        english = template["english"]

        if context:
            if "word" in context:
                vietnamese = vietnamese.replace("[word]", context["word"])
                english = english.replace("[word]", context["word"])
            if "example" in context:
                vietnamese = vietnamese.replace("[example]", context["example"])
                english = english.replace("[example]", context["example"])
            if "meaning" in context:
                vietnamese = vietnamese.replace("[meaning]", context["meaning"])
                english = english.replace("[meaning]", context["meaning"])

        self.hint_count += 1

        return BilingualHint(
            vietnamese=vietnamese,
            english=english,
            hint_level=hint_level,
            silence_duration_seconds=silence_duration_seconds,
        )

    def format_hint_for_display(self, hint: BilingualHint) -> str:
        """Format hint for display (Vietnamese first, then English).
        
        Args:
            hint: BilingualHint to format
            
        Returns:
            Formatted hint string
        """
        return f"{hint.vietnamese}\n\n{hint.english}"

    def reset_hint_count(self) -> None:
        """Reset hint count."""
        self.hint_count = 0

    def get_hint_count(self) -> int:
        """Get number of hints provided.
        
        Returns:
            Number of hints provided
        """
        return self.hint_count

    def is_scaffolding_enabled(self) -> bool:
        """Check if scaffolding is enabled.
        
        Returns:
            True if scaffolding is enabled, False otherwise
        """
        return self.enable_scaffolding
