"""Bedrock Guardrails for Content Filtering."""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ContentCategory(Enum):
    """Content categories for filtering."""
    HATE = "hate"
    INSULTS = "insults"
    SEXUAL = "sexual"
    VIOLENCE = "violence"
    PROFANITY = "profanity"


class GuardrailAction(Enum):
    """Actions for guardrail violations."""
    BLOCK = "block"  # Block the response
    FILTER = "filter"  # Filter the response
    WARN = "warn"  # Warn the user


@dataclass
class GuardrailViolation:
    """Guardrail violation details."""
    category: ContentCategory
    severity: str  # "low", "medium", "high"
    confidence: float  # 0.0-1.0
    reason: str


@dataclass
class GuardrailResult:
    """Result of guardrail check."""
    is_safe: bool
    violations: list  # List of GuardrailViolation
    action: GuardrailAction
    filtered_content: Optional[str]


class BedrockGuardrails:
    """Bedrock Guardrails for content filtering."""

    # Content filter configuration
    _CONTENT_FILTERS = {
        ContentCategory.HATE: {
            "enabled": True,
            "action": GuardrailAction.BLOCK,
            "severity_threshold": "medium",
        },
        ContentCategory.INSULTS: {
            "enabled": True,
            "action": GuardrailAction.FILTER,
            "severity_threshold": "medium",
        },
        ContentCategory.SEXUAL: {
            "enabled": True,
            "action": GuardrailAction.BLOCK,
            "severity_threshold": "low",
        },
        ContentCategory.VIOLENCE: {
            "enabled": True,
            "action": GuardrailAction.BLOCK,
            "severity_threshold": "medium",
        },
        ContentCategory.PROFANITY: {
            "enabled": True,
            "action": GuardrailAction.FILTER,
            "severity_threshold": "low",
        },
    }

    # Denied topics (non-learning topics)
    _DENIED_TOPICS = [
        "politics",
        "religion",
        "violence",
        "illegal activities",
        "adult content",
    ]

    def __init__(self, enable_guardrails: bool = True, guardrail_id: Optional[str] = None):
        """Initialize Bedrock Guardrails.
        
        Args:
            enable_guardrails: Whether to enable guardrails
            guardrail_id: AWS Bedrock Guardrail ID (optional)
        """
        self.enable_guardrails = enable_guardrails
        self.guardrail_id = guardrail_id
        self.violation_count = 0  # Track violations

    def check_content(self, content: str) -> GuardrailResult:
        """Check content against guardrails.
        
        Args:
            content: Content to check
            
        Returns:
            GuardrailResult with safety assessment
        """
        if not self.enable_guardrails:
            return GuardrailResult(
                is_safe=True,
                violations=[],
                action=GuardrailAction.WARN,
                filtered_content=None,
            )

        if not content or not content.strip():
            return GuardrailResult(
                is_safe=True,
                violations=[],
                action=GuardrailAction.WARN,
                filtered_content=None,
            )

        # Check for violations
        violations = self._detect_violations(content)

        if not violations:
            return GuardrailResult(
                is_safe=True,
                violations=[],
                action=GuardrailAction.WARN,
                filtered_content=None,
            )

        # Determine action based on violations
        action = self._determine_action(violations)
        filtered_content = self._filter_content(content, violations) if action == GuardrailAction.FILTER else None

        self.violation_count += len(violations)

        return GuardrailResult(
            is_safe=False,
            violations=violations,
            action=action,
            filtered_content=filtered_content,
        )

    def _detect_violations(self, content: str) -> list:
        """Detect guardrail violations in content.
        
        Args:
            content: Content to check
            
        Returns:
            List of GuardrailViolation
        """
        violations = []

        # Check for denied topics
        for topic in self._DENIED_TOPICS:
            if topic.lower() in content.lower():
                violations.append(
                    GuardrailViolation(
                        category=ContentCategory.PROFANITY,
                        severity="medium",
                        confidence=0.8,
                        reason=f"Denied topic: {topic}",
                    )
                )

        return violations

    def _determine_action(self, violations: list) -> GuardrailAction:
        """Determine action based on violations.
        
        Args:
            violations: List of GuardrailViolation
            
        Returns:
            GuardrailAction
        """
        if not violations:
            return GuardrailAction.WARN

        # If any violation is high severity, block
        for violation in violations:
            if violation.severity == "high":
                return GuardrailAction.BLOCK

        # If any violation is medium severity, filter
        for violation in violations:
            if violation.severity == "medium":
                return GuardrailAction.FILTER

        # Otherwise warn
        return GuardrailAction.WARN

    def _filter_content(self, content: str, violations: list) -> str:
        """Filter content to remove violations.
        
        Args:
            content: Content to filter
            violations: List of GuardrailViolation
            
        Returns:
            Filtered content
        """
        filtered = content

        # Replace denied topics with [filtered]
        for topic in self._DENIED_TOPICS:
            filtered = filtered.replace(topic, "[filtered]")
            filtered = filtered.replace(topic.capitalize(), "[filtered]")
            filtered = filtered.replace(topic.upper(), "[filtered]")

        return filtered

    def should_block(self, content: str) -> bool:
        """Determine if content should be blocked.
        
        Args:
            content: Content to check
            
        Returns:
            True if content should be blocked, False otherwise
        """
        result = self.check_content(content)
        return result.action == GuardrailAction.BLOCK

    def should_filter(self, content: str) -> bool:
        """Determine if content should be filtered.
        
        Args:
            content: Content to check
            
        Returns:
            True if content should be filtered, False otherwise
        """
        result = self.check_content(content)
        return result.action == GuardrailAction.FILTER

    def get_violation_message(self, result: GuardrailResult) -> str:
        """Get user-friendly violation message.
        
        Args:
            result: GuardrailResult
            
        Returns:
            Violation message
        """
        if result.is_safe:
            return "Content is safe."

        if result.action == GuardrailAction.BLOCK:
            return "This content violates our content policy and cannot be displayed."

        if result.action == GuardrailAction.FILTER:
            return "This content has been filtered to comply with our content policy."

        return "This content may violate our content policy. Please review."

    def reset_violation_count(self) -> None:
        """Reset violation count."""
        self.violation_count = 0

    def get_violation_count(self) -> int:
        """Get number of violations detected.
        
        Returns:
            Number of violations
        """
        return self.violation_count

    def is_guardrails_enabled(self) -> bool:
        """Check if guardrails are enabled.
        
        Returns:
            True if guardrails are enabled, False otherwise
        """
        return self.enable_guardrails

    def get_violation_rate(self, total_checks: int) -> float:
        """Get violation rate.
        
        Args:
            total_checks: Total number of checks
            
        Returns:
            Violation rate (0.0-1.0)
        """
        if total_checks == 0:
            return 0.0
        return self.violation_count / total_checks

    def add_denied_topic(self, topic: str) -> None:
        """Add a denied topic.
        
        Args:
            topic: Topic to deny
        """
        if topic not in self._DENIED_TOPICS:
            self._DENIED_TOPICS.append(topic)

    def remove_denied_topic(self, topic: str) -> None:
        """Remove a denied topic.
        
        Args:
            topic: Topic to remove
        """
        if topic in self._DENIED_TOPICS:
            self._DENIED_TOPICS.remove(topic)

    def get_denied_topics(self) -> list:
        """Get list of denied topics.
        
        Returns:
            List of denied topics
        """
        return self._DENIED_TOPICS.copy()

    def set_content_filter(
        self,
        category: ContentCategory,
        enabled: bool,
        action: GuardrailAction,
    ) -> None:
        """Set content filter configuration.
        
        Args:
            category: Content category
            enabled: Whether to enable filter
            action: Action to take on violation
        """
        self._CONTENT_FILTERS[category] = {
            "enabled": enabled,
            "action": action,
            "severity_threshold": self._CONTENT_FILTERS[category].get("severity_threshold", "medium"),
        }

    def get_content_filter(self, category: ContentCategory) -> dict:
        """Get content filter configuration.
        
        Args:
            category: Content category
            
        Returns:
            Filter configuration
        """
        return self._CONTENT_FILTERS.get(category, {})
