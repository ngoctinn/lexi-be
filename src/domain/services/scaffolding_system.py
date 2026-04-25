"""Bilingual Scaffolding System for A1-A2 learners."""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


@dataclass
class ScaffoldingContext:
    """Context for generating context-aware hints."""
    scenario_title: Optional[str] = None
    scenario_vocabulary: Optional[List[str]] = None
    last_utterance: Optional[str] = None
    conversation_goals: Optional[List[str]] = None


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
    
    def to_markdown_format(self) -> dict:
        """Convert to markdown format for frontend display.
        
        Returns:
            Dictionary with formatted content for frontend
        """
        return {
            "vietnamese": {
                "content": self.vietnamese,
                "formatted": f"💡 **Gợi ý:** {self.vietnamese}"
            },
            "english": {
                "content": self.english, 
                "formatted": f"💡 **Hint:** {self.english}"
            },
            "hint_level": self.hint_level.value,
            "silence_duration": self.silence_duration_seconds,
            "display_format": "bilingual"  # or "vietnamese_only", "english_only"
        }
    
    def to_legacy_format(self) -> str:
        """Convert to legacy format for backward compatibility.
        
        Returns:
            Legacy format string (Vietnamese first, then English)
        """
        return f"{self.vietnamese}\n\n{self.english}"


class ScaffoldingSystem:
    """Generates bilingual hints for A1-A2 learners."""

    # Scenario vocabulary mappings (A1-A2 level)
    _SCENARIO_VOCABULARY = {
        "Restaurant": {
            "questions": [
                "Can I have the menu?",
                "What do you recommend?",
                "How much is this?",
                "Can I order now?",
                "Where is the bathroom?",
            ],
            "statements": [
                "I'd like to order...",
                "This looks delicious",
                "The bill, please",
                "I'm allergic to...",
                "Can I have water?",
            ],
        },
        "Airport": {
            "questions": [
                "Where is gate...?",
                "When does the flight leave?",
                "Can I check in here?",
                "Where is my luggage?",
                "Do I need a boarding pass?",
            ],
            "statements": [
                "I need to check in",
                "Here's my passport",
                "I have two bags",
                "I'm flying to...",
                "My flight is delayed",
            ],
        },
        "Hotel": {
            "questions": [
                "Do you have rooms available?",
                "How much is a room?",
                "Can I check in now?",
                "Where is the elevator?",
                "What time is breakfast?",
            ],
            "statements": [
                "I have a reservation",
                "I'd like a room for two nights",
                "Can I have a wake-up call?",
                "The room is too cold",
                "I need extra towels",
            ],
        },
        "Shopping": {
            "questions": [
                "How much is this?",
                "Do you have this in a different size?",
                "Can I try this on?",
                "Where is the fitting room?",
                "Do you accept credit cards?",
            ],
            "statements": [
                "I'm looking for...",
                "This is too expensive",
                "I'll take this one",
                "Can I get a discount?",
                "I'd like to return this",
            ],
        },
        # Fallback for general conversation
        "General": {
            "questions": [
                "Can you tell me more?",
                "What do you think?",
                "How do you feel about that?",
                "Why do you say that?",
                "What happened next?",
            ],
            "statements": [
                "I think...",
                "I believe...",
                "In my opinion...",
                "That's interesting",
                "I agree/disagree",
            ],
        },
    }

    # Grammar pattern keywords for detection
    _GRAMMAR_PATTERNS = {
        "past_tense": ["yesterday", "last", "ago", "was", "were", "did"],
        "present_tense": ["now", "today", "always", "usually", "often", "sometimes"],
        "question": ["what", "where", "when", "why", "how", "who", "?"],
    }

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
            context: Optional context (scenario_title, last_utterance, etc.)
            
        Returns:
            BilingualHint or None if no hint should be provided
        """
        if not self.should_provide_hint(silence_duration_seconds, proficiency_level):
            return None

        hint_level = self.get_hint_level(silence_duration_seconds)
        if not hint_level:
            return None

        # Generate context-aware hint if context provided
        if context:
            hint = self._generate_context_aware_hint(
                proficiency_level, hint_level, context
            )
        else:
            # Fallback to generic hint (backward compatibility)
            hint = self._generate_generic_hint(proficiency_level, hint_level)

        self.hint_count += 1
        return hint

    def format_hint_for_display(self, hint: BilingualHint, format_type: str = "legacy") -> str | dict:
        """Format hint for display with multiple format options.
        
        Args:
            hint: BilingualHint to format
            format_type: "legacy" (backward compatible), "markdown", or "structured"
            
        Returns:
            Formatted hint string or structured dict
        """
        if format_type == "markdown":
            return hint.to_markdown_format()
        elif format_type == "structured":
            return {
                "vietnamese": hint.vietnamese,
                "english": hint.english,
                "hint_level": hint.hint_level.value,
                "silence_duration": hint.silence_duration_seconds
            }
        else:  # legacy format (default)
            return hint.to_legacy_format()

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

    def _detect_grammar_pattern(self, utterance: str) -> Optional[str]:
        """Detect grammar pattern using simple keyword matching.
        
        Args:
            utterance: Learner's utterance
            
        Returns:
            Pattern name ("past_tense", "present_tense", "question", "short_response") or None
        """
        if not utterance:
            return None
        
        utterance_lower = utterance.lower()
        
        # Check for past tense indicators (before short response check)
        if any(keyword in utterance_lower for keyword in self._GRAMMAR_PATTERNS["past_tense"]):
            return "past_tense"
        
        # Check for present tense indicators
        if any(keyword in utterance_lower for keyword in self._GRAMMAR_PATTERNS["present_tense"]):
            return "present_tense"
        
        # Check for question patterns
        if any(keyword in utterance_lower for keyword in self._GRAMMAR_PATTERNS["question"]):
            return "question"
        
        # Check for short responses (< 5 words) - vocabulary gap
        if len(utterance.split()) < 5:
            return "short_response"
        
        return None

    def _get_scenario_vocabulary(self, scenario_title: str) -> dict:
        """Get vocabulary for scenario with fallback.
        
        Args:
            scenario_title: Scenario title
            
        Returns:
            Dictionary with "questions" and "statements" lists
        """
        return self._SCENARIO_VOCABULARY.get(scenario_title, self._SCENARIO_VOCABULARY["General"])

    def _generate_context_aware_hint(
        self,
        proficiency_level: str,
        hint_level: HintLevel,
        context: dict,
    ) -> BilingualHint:
        """Generate hint using scenario and learner context.
        
        Args:
            proficiency_level: Proficiency level (A1, A2)
            hint_level: Hint level to generate
            context: Context dictionary with scenario_title, last_utterance, etc.
            
        Returns:
            BilingualHint with context-aware content
        """
        scenario_title = context.get("scenario_title", "")
        last_utterance = context.get("last_utterance", "")
        
        # Get scenario-specific vocabulary
        vocabulary = self._get_scenario_vocabulary(scenario_title)
        
        # Detect grammar pattern in last utterance
        grammar_pattern = self._detect_grammar_pattern(last_utterance)
        
        # Generate hint based on level and context
        if hint_level == HintLevel.VOCABULARY_HINT:
            return self._generate_vocabulary_hint_with_context(
                proficiency_level, vocabulary, grammar_pattern
            )
        elif hint_level == HintLevel.SENTENCE_STARTER:
            return self._generate_sentence_starter_with_context(
                proficiency_level, vocabulary, grammar_pattern
            )
        else:
            # Gentle prompt doesn't need context
            return self._generate_generic_hint(proficiency_level, hint_level)

    def _generate_vocabulary_hint_with_context(
        self,
        proficiency_level: str,
        vocabulary: dict,
        grammar_pattern: Optional[str],
    ) -> BilingualHint:
        """Generate vocabulary hint using scenario vocabulary and grammar pattern.
        
        Args:
            proficiency_level: Proficiency level (A1, A2)
            vocabulary: Scenario vocabulary dict
            grammar_pattern: Detected grammar pattern
            
        Returns:
            BilingualHint with context-aware vocabulary suggestions
        """
        # Select vocabulary based on grammar pattern
        if grammar_pattern == "question":
            phrases = vocabulary.get("questions", [])
        else:
            phrases = vocabulary.get("statements", [])
        
        # Pick first 2 phrases as examples
        examples = phrases[:2] if phrases else ["I think...", "I believe..."]
        
        if proficiency_level == "A1":
            vietnamese = f"Bạn có thể dùng: '{examples[0]}' hoặc '{examples[1] if len(examples) > 1 else examples[0]}'"
            english = f"You can use: '{examples[0]}' or '{examples[1] if len(examples) > 1 else examples[0]}'"
        else:  # A2
            vietnamese = f"Hãy thử: '{examples[0]}' hoặc '{examples[1] if len(examples) > 1 else examples[0]}'"
            english = f"Try: '{examples[0]}' or '{examples[1] if len(examples) > 1 else examples[0]}'"
        
        return BilingualHint(
            vietnamese=vietnamese,
            english=english,
            hint_level=HintLevel.VOCABULARY_HINT,
            silence_duration_seconds=20,
        )

    def _generate_sentence_starter_with_context(
        self,
        proficiency_level: str,
        vocabulary: dict,
        grammar_pattern: Optional[str],
    ) -> BilingualHint:
        """Generate sentence starter using scenario vocabulary and grammar pattern.
        
        Args:
            proficiency_level: Proficiency level (A1, A2)
            vocabulary: Scenario vocabulary dict
            grammar_pattern: Detected grammar pattern
            
        Returns:
            BilingualHint with context-aware sentence starters
        """
        # Select vocabulary based on grammar pattern
        if grammar_pattern == "question":
            phrases = vocabulary.get("questions", [])
        elif grammar_pattern == "past_tense":
            # For past tense, suggest past tense starters
            phrases = ["I went...", "I did...", "I was..."]
        elif grammar_pattern == "present_tense":
            # For present tense, suggest present tense starters
            phrases = ["I go...", "I do...", "I am..."]
        else:
            phrases = vocabulary.get("statements", [])
        
        # Pick first 2 phrases as examples
        examples = phrases[:2] if phrases else ["I think...", "I believe..."]
        
        if proficiency_level == "A1":
            vietnamese = f"Bạn có thể bắt đầu: '{examples[0]}' hoặc '{examples[1] if len(examples) > 1 else examples[0]}'"
            english = f"You can start with: '{examples[0]}' or '{examples[1] if len(examples) > 1 else examples[0]}'"
        else:  # A2
            vietnamese = f"Hãy bắt đầu: '{examples[0]}' hoặc '{examples[1] if len(examples) > 1 else examples[0]}'"
            english = f"Start with: '{examples[0]}' or '{examples[1] if len(examples) > 1 else examples[0]}'"
        
        return BilingualHint(
            vietnamese=vietnamese,
            english=english,
            hint_level=HintLevel.SENTENCE_STARTER,
            silence_duration_seconds=30,
        )

    def _generate_generic_hint(
        self,
        proficiency_level: str,
        hint_level: HintLevel,
    ) -> BilingualHint:
        """Generate generic hint (fallback when no context available).
        
        Args:
            proficiency_level: Proficiency level (A1, A2)
            hint_level: Hint level to generate
            
        Returns:
            BilingualHint with generic content
        """
        if hint_level == HintLevel.GENTLE_PROMPT:
            template = self._GENTLE_PROMPTS.get(proficiency_level)
            silence_duration = 10
        elif hint_level == HintLevel.VOCABULARY_HINT:
            template = self._VOCABULARY_HINTS.get(proficiency_level)
            silence_duration = 20
        elif hint_level == HintLevel.SENTENCE_STARTER:
            template = self._SENTENCE_STARTERS.get(proficiency_level)
            silence_duration = 30
        else:
            template = self._GENTLE_PROMPTS.get(proficiency_level)
            silence_duration = 10
        
        if not template:
            template = self._GENTLE_PROMPTS.get("A1")
            silence_duration = 10
        
        return BilingualHint(
            vietnamese=template["vietnamese"],
            english=template["english"],
            hint_level=hint_level,
            silence_duration_seconds=silence_duration,
        )
