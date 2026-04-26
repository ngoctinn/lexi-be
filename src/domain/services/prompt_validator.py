"""Validator for AI-generated prompts to ensure English examples are not translated."""

import re
import logging

logger = logging.getLogger(__name__)


def has_vietnamese_text(text: str) -> bool:
    """
    Check if text contains Vietnamese characters.
    
    Vietnamese uses Latin characters with diacritics (à, á, ả, ã, ạ, etc.)
    and some special characters.
    
    Args:
        text: Text to check
        
    Returns:
        True if Vietnamese text detected, False otherwise
    """
    # Vietnamese diacritics pattern
    vietnamese_pattern = r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]'
    return bool(re.search(vietnamese_pattern, text, re.IGNORECASE))


def validate_example_language(example_text: str) -> tuple[bool, str]:
    """
    Validate that example text is in English, not Vietnamese.
    
    Args:
        example_text: Example text to validate (e.g., "I went to school")
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if example is in English
        - error_message: Description of issue if invalid
    """
    if not example_text or not example_text.strip():
        return True, ""
    
    # Check for Vietnamese text in example
    if has_vietnamese_text(example_text):
        return False, "Example contains Vietnamese text - must be in English"
    
    return True, ""


def validate_conversation_analyzer_response(response_data: dict) -> tuple[bool, list[str]]:
    """
    Validate conversation analyzer response structure and content.
    
    Args:
        response_data: Parsed JSON response from analyzer
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    required_fields = ["mistakes_vi", "mistakes_en", "improvements_vi", "improvements_en"]
    for field in required_fields:
        if field not in response_data:
            errors.append(f"Missing required field: {field}")
    
    # Validate mistakes_vi contains English examples
    mistakes_vi = response_data.get("mistakes_vi", [])
    for i, mistake in enumerate(mistakes_vi):
        if not isinstance(mistake, str):
            errors.append(f"mistakes_vi[{i}] is not a string")
            continue
        
        # Extract the part between ~~ and ** (the example)
        # Pattern: ~~[english]~~ ... **[english]**
        english_parts = re.findall(r'~~([^~]+)~~|\*\*([^*]+)\*\*', mistake)
        for part in english_parts:
            example = part[0] or part[1]  # Get non-empty group
            is_valid, error_msg = validate_example_language(example)
            if not is_valid:
                errors.append(f"mistakes_vi[{i}]: {error_msg} - '{example}'")
    
    # Validate improvements_vi contains English examples
    improvements_vi = response_data.get("improvements_vi", [])
    for i, improvement in enumerate(improvements_vi):
        if not isinstance(improvement, str):
            errors.append(f"improvements_vi[{i}] is not a string")
            continue
        
        # Extract the part between ** (the example)
        english_parts = re.findall(r'\*\*([^*]+)\*\*', improvement)
        for part in english_parts:
            is_valid, error_msg = validate_example_language(part)
            if not is_valid:
                errors.append(f"improvements_vi[{i}]: {error_msg} - '{part}'")
    
    return len(errors) == 0, errors


def validate_structured_hint_response(response_data: dict) -> tuple[bool, list[str]]:
    """
    Validate structured hint response structure and content.
    
    Args:
        response_data: Parsed JSON response from hint generator
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    required_fields = ["level", "type", "markdown_vi", "markdown_en"]
    for field in required_fields:
        if field not in response_data:
            errors.append(f"Missing required field: {field}")
    
    # Validate markdown_vi contains English examples
    markdown_vi = response_data.get("markdown_vi", "")
    if not isinstance(markdown_vi, str):
        errors.append("markdown_vi is not a string")
    else:
        # Extract examples between ** (bold text)
        examples = re.findall(r'\*\*([^*]+)\*\*', markdown_vi)
        for example in examples:
            # Skip if it's a grammar term like "simple present tense"
            if any(term in example.lower() for term in ["tense", "verb", "noun", "adjective", "adverb"]):
                continue
            
            # Check if it looks like a sentence (has spaces and common English words)
            if len(example.split()) > 2:  # Multi-word example
                is_valid, error_msg = validate_example_language(example)
                if not is_valid:
                    errors.append(f"markdown_vi: {error_msg} - '{example}'")
    
    return len(errors) == 0, errors


def log_validation_errors(errors: list[str], context: str = ""):
    """Log validation errors with context."""
    if errors:
        logger.warning(
            f"Validation errors detected{' in ' + context if context else ''}",
            extra={
                "error_count": len(errors),
                "errors": errors,
            }
        )
