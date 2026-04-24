"""Vietnamese Language Detection using AWS Comprehend."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LanguageDetectionResult:
    """Result of language detection."""
    language_code: str  # e.g., "vi", "en"
    language_name: str  # e.g., "Vietnamese", "English"
    confidence: float  # 0.0-1.0
    is_vietnamese: bool


class VietnameseDetector:
    """Detects Vietnamese language in learner input using AWS Comprehend."""

    # Common Vietnamese language codes
    VIETNAMESE_CODES = ["vi", "vie"]
    ENGLISH_CODES = ["en", "eng"]

    def __init__(self, comprehend_client=None):
        """Initialize Vietnamese detector.
        
        Args:
            comprehend_client: AWS Comprehend client (optional for testing)
        """
        self.comprehend_client = comprehend_client

    def detect_language(self, text: str) -> LanguageDetectionResult:
        """Detect language of input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            LanguageDetectionResult with detection details
        """
        if not text or not text.strip():
            return LanguageDetectionResult(
                language_code="unknown",
                language_name="Unknown",
                confidence=0.0,
                is_vietnamese=False,
            )

        # If Comprehend client available, use it
        if self.comprehend_client:
            return self._detect_with_comprehend(text)

        # Fallback: simple heuristic detection
        return self._detect_with_heuristic(text)

    def _detect_with_comprehend(self, text: str) -> LanguageDetectionResult:
        """Detect language using AWS Comprehend.
        
        Args:
            text: Input text to analyze
            
        Returns:
            LanguageDetectionResult
        """
        try:
            response = self.comprehend_client.detect_dominant_language(Text=text)
            
            if not response.get("Languages"):
                return LanguageDetectionResult(
                    language_code="unknown",
                    language_name="Unknown",
                    confidence=0.0,
                    is_vietnamese=False,
                )

            # Get top language
            top_language = response["Languages"][0]
            language_code = top_language.get("LanguageCode", "unknown")
            confidence = top_language.get("Score", 0.0)

            # Map language code to name
            language_name = self._get_language_name(language_code)
            is_vietnamese = language_code in self.VIETNAMESE_CODES

            return LanguageDetectionResult(
                language_code=language_code,
                language_name=language_name,
                confidence=confidence,
                is_vietnamese=is_vietnamese,
            )
        except Exception as e:
            # Fallback to heuristic if Comprehend fails
            return self._detect_with_heuristic(text)

    def _detect_with_heuristic(self, text: str) -> LanguageDetectionResult:
        """Detect language using heuristic (Vietnamese character detection).
        
        Args:
            text: Input text to analyze
            
        Returns:
            LanguageDetectionResult
        """
        # Vietnamese-specific characters (diacritics)
        vietnamese_chars = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ")
        
        # Count Vietnamese characters
        text_lower = text.lower()
        vietnamese_count = sum(1 for char in text_lower if char in vietnamese_chars)
        total_chars = len([c for c in text_lower if c.isalpha()])

        if total_chars == 0:
            return LanguageDetectionResult(
                language_code="unknown",
                language_name="Unknown",
                confidence=0.0,
                is_vietnamese=False,
            )

        # Calculate confidence
        confidence = vietnamese_count / total_chars if total_chars > 0 else 0.0

        # If > 10% Vietnamese characters, likely Vietnamese
        is_vietnamese = confidence > 0.1

        language_code = "vi" if is_vietnamese else "en"
        language_name = "Vietnamese" if is_vietnamese else "English"

        return LanguageDetectionResult(
            language_code=language_code,
            language_name=language_name,
            confidence=confidence,
            is_vietnamese=is_vietnamese,
        )

    def _get_language_name(self, language_code: str) -> str:
        """Get language name from code.
        
        Args:
            language_code: Language code (e.g., "vi", "en")
            
        Returns:
            Language name
        """
        language_map = {
            "vi": "Vietnamese",
            "vie": "Vietnamese",
            "en": "English",
            "eng": "English",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "pt": "Portuguese",
            "ja": "Japanese",
            "zh": "Chinese",
            "ko": "Korean",
        }
        return language_map.get(language_code, "Unknown")

    def should_redirect_to_english(
        self,
        text: str,
        confidence_threshold: float = 0.5,
    ) -> bool:
        """Determine if learner should be redirected to English.
        
        Args:
            text: Input text to analyze
            confidence_threshold: Confidence threshold for Vietnamese detection
            
        Returns:
            True if learner should be redirected, False otherwise
        """
        result = self.detect_language(text)
        return result.is_vietnamese and result.confidence >= confidence_threshold

    def get_redirect_message(self) -> dict:
        """Get redirect message for Vietnamese learner.
        
        Returns:
            Dictionary with Vietnamese and English redirect messages
        """
        return {
            "vietnamese": "Hãy thử nói tiếng Anh! Tôi sẽ giúp bạn.",
            "english": "Please try in English! I'll help you.",
        }

    def get_follow_up_prompt(self, proficiency_level: str) -> dict:
        """Get follow-up prompt after redirect.
        
        Args:
            proficiency_level: Proficiency level (A1, A2, etc.)
            
        Returns:
            Dictionary with Vietnamese and English prompts
        """
        prompts = {
            "A1": {
                "vietnamese": "Bạn có thể nói gì về chủ đề này bằng tiếng Anh?",
                "english": "What can you say about this topic in English?",
            },
            "A2": {
                "vietnamese": "Hãy thử lại bằng tiếng Anh. Bạn có thể làm được!",
                "english": "Try again in English. You can do it!",
            },
            "B1": {
                "vietnamese": "Vui lòng tiếp tục bằng tiếng Anh.",
                "english": "Please continue in English.",
            },
            "B2": {
                "vietnamese": "Hãy sử dụng tiếng Anh để trả lời.",
                "english": "Please use English to respond.",
            },
            "C1": {
                "vietnamese": "Tiếp tục bằng tiếng Anh.",
                "english": "Continue in English.",
            },
            "C2": {
                "vietnamese": "Tiếp tục bằng tiếng Anh.",
                "english": "Continue in English.",
            },
        }
        return prompts.get(proficiency_level, prompts["A1"])

    def get_detection_confidence(self, text: str) -> float:
        """Get confidence score for Vietnamese detection.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Confidence score (0.0-1.0)
        """
        result = self.detect_language(text)
        return result.confidence if result.is_vietnamese else 0.0
