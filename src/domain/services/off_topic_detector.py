"""Off-Topic Detection and Redirect System."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class OffTopicSeverity(Enum):
    """Severity levels for off-topic messages."""
    MILD = "mild"  # Slightly off-topic, gentle redirect
    MODERATE = "moderate"  # Clearly off-topic, firm redirect
    SEVERE = "severe"  # Completely off-topic, strong redirect


@dataclass
class OffTopicDetectionResult:
    """Result of off-topic detection."""
    is_off_topic: bool
    severity: Optional[OffTopicSeverity]
    confidence: float  # 0.0-1.0
    reason: Optional[str]


@dataclass
class RedirectMessage:
    """Redirect message for off-topic learner."""
    vietnamese: str
    english: str
    severity: OffTopicSeverity


class OffTopicDetector:
    """Detects off-topic messages and generates redirects."""

    # Off-topic redirect templates per severity
    _REDIRECT_TEMPLATES = {
        OffTopicSeverity.MILD: {
            "vietnamese": "Đó là một ý tưởng thú vị! Nhưng hãy tập trung vào [scenario]. Bạn có thể nói gì về [scenario]?",
            "english": "That's an interesting idea! But let's focus on [scenario]. What can you say about [scenario]?",
        },
        OffTopicSeverity.MODERATE: {
            "vietnamese": "Hãy tập trung vào chủ đề [scenario]. Hãy nói về [scenario].",
            "english": "Let's focus on [scenario]. Please talk about [scenario].",
        },
        OffTopicSeverity.SEVERE: {
            "vietnamese": "Chúng ta cần tập trung vào [scenario]. Hãy trả lời câu hỏi về [scenario].",
            "english": "We need to focus on [scenario]. Please answer the question about [scenario].",
        },
    }

    def __init__(self, enable_detection: bool = True):
        """Initialize off-topic detector.
        
        Args:
            enable_detection: Whether to enable off-topic detection
        """
        self.enable_detection = enable_detection
        self.off_topic_count = 0  # Track off-topic messages

    def detect_off_topic(
        self,
        message: str,
        scenario_title: str,
        proficiency_level: str,
    ) -> OffTopicDetectionResult:
        """Detect if message is off-topic.
        
        Note: This is a placeholder. In production, this would use:
        1. Prompt instruction to AI model
        2. Semantic similarity to scenario
        3. Keyword matching
        
        Args:
            message: Learner message
            scenario_title: Current scenario (e.g., "Restaurant", "Hotel")
            proficiency_level: Proficiency level (A1-C2)
            
        Returns:
            OffTopicDetectionResult
        """
        if not self.enable_detection:
            return OffTopicDetectionResult(
                is_off_topic=False,
                severity=None,
                confidence=0.0,
                reason=None,
            )

        if not message or not message.strip():
            return OffTopicDetectionResult(
                is_off_topic=False,
                severity=None,
                confidence=0.0,
                reason=None,
            )

        # Placeholder: In production, use AI model or semantic similarity
        # For now, use simple heuristic
        return self._detect_with_heuristic(message, scenario_title)

    def _detect_with_heuristic(
        self,
        message: str,
        scenario_title: str,
    ) -> OffTopicDetectionResult:
        """Detect off-topic using heuristic (placeholder).
        
        Args:
            message: Learner message
            scenario_title: Current scenario
            
        Returns:
            OffTopicDetectionResult
        """
        # Simple heuristic: check if scenario keywords are in message
        scenario_keywords = self._get_scenario_keywords(scenario_title)
        message_lower = message.lower()

        # Count keyword matches
        keyword_matches = sum(
            1 for keyword in scenario_keywords
            if keyword.lower() in message_lower
        )

        # If no keywords found, likely off-topic
        if keyword_matches == 0:
            # Determine severity based on message length
            if len(message) < 10:
                severity = OffTopicSeverity.MILD
            elif len(message) < 50:
                severity = OffTopicSeverity.MODERATE
            else:
                severity = OffTopicSeverity.SEVERE

            return OffTopicDetectionResult(
                is_off_topic=True,
                severity=severity,
                confidence=0.7,  # Moderate confidence
                reason=f"No keywords from scenario '{scenario_title}' found",
            )

        return OffTopicDetectionResult(
            is_off_topic=False,
            severity=None,
            confidence=0.0,
            reason=None,
        )

    def _get_scenario_keywords(self, scenario_title: str) -> list:
        """Get keywords for a scenario.
        
        Args:
            scenario_title: Scenario title (e.g., "Restaurant")
            
        Returns:
            List of keywords
        """
        scenario_keywords = {
            "Restaurant": ["restaurant", "food", "menu", "order", "eat", "drink", "waiter", "table"],
            "Hotel": ["hotel", "room", "check-in", "check-out", "reservation", "booking", "guest"],
            "Airport": ["airport", "flight", "boarding", "gate", "luggage", "ticket", "passenger"],
            "Shopping": ["shop", "store", "buy", "price", "product", "customer", "cashier"],
            "Hospital": ["hospital", "doctor", "patient", "medicine", "appointment", "nurse"],
            "School": ["school", "class", "teacher", "student", "lesson", "homework", "exam"],
            "Park": ["park", "walk", "play", "bench", "tree", "grass", "outdoor"],
            "Library": ["library", "book", "read", "borrow", "librarian", "shelf"],
        }
        return scenario_keywords.get(scenario_title, [scenario_title.lower()])

    def should_redirect(
        self,
        message: str,
        scenario_title: str,
        proficiency_level: str,
    ) -> bool:
        """Determine if learner should be redirected.
        
        Args:
            message: Learner message
            scenario_title: Current scenario
            proficiency_level: Proficiency level
            
        Returns:
            True if redirect needed, False otherwise
        """
        result = self.detect_off_topic(message, scenario_title, proficiency_level)
        return result.is_off_topic

    def generate_redirect(
        self,
        scenario_title: str,
        proficiency_level: str,
        severity: Optional[OffTopicSeverity] = None,
    ) -> Optional[RedirectMessage]:
        """Generate redirect message for off-topic learner.
        
        Args:
            scenario_title: Current scenario
            proficiency_level: Proficiency level
            severity: Severity level (auto-detect if None)
            
        Returns:
            RedirectMessage or None
        """
        if not severity:
            severity = self._get_default_severity(proficiency_level)

        template = self._REDIRECT_TEMPLATES.get(severity)
        if not template:
            return None

        # Replace scenario placeholder
        vietnamese = template["vietnamese"].replace("[scenario]", scenario_title)
        english = template["english"].replace("[scenario]", scenario_title)

        self.off_topic_count += 1

        return RedirectMessage(
            vietnamese=vietnamese,
            english=english,
            severity=severity,
        )

    def _get_default_severity(self, proficiency_level: str) -> OffTopicSeverity:
        """Get default severity for proficiency level.
        
        Args:
            proficiency_level: Proficiency level (A1-C2)
            
        Returns:
            Default severity
        """
        # A1-A2: gentle redirect
        if proficiency_level in ["A1", "A2"]:
            return OffTopicSeverity.MILD
        # B1-B2: moderate redirect
        elif proficiency_level in ["B1", "B2"]:
            return OffTopicSeverity.MODERATE
        # C1-C2: firm redirect
        else:
            return OffTopicSeverity.SEVERE

    def format_redirect_for_display(self, redirect: RedirectMessage) -> str:
        """Format redirect message for display.
        
        Args:
            redirect: RedirectMessage to format
            
        Returns:
            Formatted redirect string
        """
        return f"{redirect.vietnamese}\n\n{redirect.english}"

    def reset_off_topic_count(self) -> None:
        """Reset off-topic count."""
        self.off_topic_count = 0

    def get_off_topic_count(self) -> int:
        """Get number of off-topic messages.
        
        Returns:
            Number of off-topic messages
        """
        return self.off_topic_count

    def is_detection_enabled(self) -> bool:
        """Check if detection is enabled.
        
        Returns:
            True if detection is enabled, False otherwise
        """
        return self.enable_detection

    def get_off_topic_rate(self, total_messages: int) -> float:
        """Get off-topic rate.
        
        Args:
            total_messages: Total number of messages
            
        Returns:
            Off-topic rate (0.0-1.0)
        """
        if total_messages == 0:
            return 0.0
        return self.off_topic_count / total_messages
