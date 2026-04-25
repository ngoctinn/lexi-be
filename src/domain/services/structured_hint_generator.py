"""Structured hint generation for conversation sessions."""

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class StructuredHint:
    """Structured bilingual hint for learners."""
    
    conversation_context: dict[str, str]  # {"vi": "...", "en": "..."}
    turn_goal: dict[str, str]             # {"vi": "...", "en": "..."}
    suggested_approach: dict[str, str]    # {"vi": "...", "en": "..."}
    example_phrases: dict[str, list[str]] # {"vi": ["...", "..."], "en": ["...", "..."]}
    grammar_tip: dict[str, str]           # {"vi": "...", "en": "..."}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "conversation_context": self.conversation_context,
            "turn_goal": self.turn_goal,
            "suggested_approach": self.suggested_approach,
            "example_phrases": self.example_phrases,
            "grammar_tip": self.grammar_tip,
        }


def validate_structured_hint(hint: dict) -> bool:
    """Validate structured hint has required fields.
    
    Args:
        hint: Dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        "conversation_context",
        "turn_goal",
        "suggested_approach",
        "example_phrases",
        "grammar_tip",
    ]
    
    for field in required_fields:
        if field not in hint:
            return False
        
        # Check bilingual structure
        if not isinstance(hint[field], dict):
            return False
        
        if "vi" not in hint[field] or "en" not in hint[field]:
            return False
    
    # Check example_phrases is list
    if not isinstance(hint["example_phrases"]["vi"], list):
        return False
    if not isinstance(hint["example_phrases"]["en"], list):
        return False
    
    return True


class StructuredHintGenerator:
    """Generates structured bilingual hints for learners."""

    def __init__(self, bedrock_client):
        """Initialize StructuredHintGenerator with Bedrock client.
        
        Args:
            bedrock_client: boto3 Bedrock Runtime client
        """
        self._bedrock = bedrock_client

    def generate(
        self,
        session: Any,
        last_ai_turn: Optional[Any],
        turn_history: list[Any],
    ) -> StructuredHint:
        """Generate structured bilingual hint.
        
        Args:
            session: Session entity with level, selected_goals, learner_role_id
            last_ai_turn: Last AI turn (or None if no AI turns yet)
            turn_history: List of Turn entities
            
        Returns:
            StructuredHint with bilingual fields
            
        Raises:
            ValueError: If validation fails
            Exception: If Bedrock call fails
        """
        import time
        start_time = time.time()
        session_id = str(getattr(session, 'session_id', 'unknown'))
        turn_index = len(turn_history)
        
        try:
            # Build prompt with context
            prompt = self._build_prompt(session, last_ai_turn, turn_history)
            
            # Call Bedrock
            hint_data, input_tokens, output_tokens = self._call_bedrock(prompt)
            
            # Validate response
            if not validate_structured_hint(hint_data):
                raise ValueError("Invalid structured hint response from Bedrock")
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            
            # Estimate cost (Amazon Nova Micro pricing)
            cost_usd = (input_tokens / 1000 * 0.000035) + (output_tokens / 1000 * 0.00014)
            
            # Log performance metrics
            logger.info(
                "Structured hint generated successfully",
                extra={
                    "session_id": session_id,
                    "turn_index": turn_index,
                    "latency_ms": round(latency_ms, 2),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": round(cost_usd, 6),
                }
            )
            
            # Return StructuredHint dataclass
            return StructuredHint(
                conversation_context=hint_data["conversation_context"],
                turn_goal=hint_data["turn_goal"],
                suggested_approach=hint_data["suggested_approach"],
                example_phrases=hint_data["example_phrases"],
                grammar_tip=hint_data["grammar_tip"],
            )
            
        except json.JSONDecodeError as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(
                "JSON parsing failed for structured hint",
                extra={
                    "session_id": session_id,
                    "turn_index": turn_index,
                    "latency_ms": round(latency_ms, 2),
                    "error": str(e),
                }
            )
            raise
            
        except ValueError as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(
                "Validation failed for structured hint",
                extra={
                    "session_id": session_id,
                    "turn_index": turn_index,
                    "latency_ms": round(latency_ms, 2),
                    "error": str(e),
                }
            )
            raise
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(
                "Structured hint generation failed",
                extra={
                    "session_id": session_id,
                    "turn_index": turn_index,
                    "latency_ms": round(latency_ms, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )
            raise

    def _build_prompt(
        self,
        session: Any,
        last_ai_turn: Optional[Any],
        turn_history: list[Any],
    ) -> str:
        """Build prompt for Bedrock.
        
        Args:
            session: Session entity
            last_ai_turn: Last AI turn (or None)
            turn_history: List of Turn entities
            
        Returns:
            Prompt string
        """
        # Extract context
        last_ai_content = last_ai_turn.content if last_ai_turn else "No AI message yet"
        current_goal = session.selected_goals[0] if session.selected_goals else "general conversation"
        
        prompt = f"""You are an English tutor providing structured hints to Vietnamese learners.

Generate a structured hint for this conversation:
- Last AI message: "{last_ai_content}"
- Learner level: {session.level}
- Current goal: {current_goal}
- Learner role: {session.learner_role_id}

Provide a JSON response with these fields (all bilingual Vietnamese/English):
{{
  "conversation_context": {{"vi": "...", "en": "..."}},
  "turn_goal": {{"vi": "...", "en": "..."}},
  "suggested_approach": {{"vi": "...", "en": "..."}},
  "example_phrases": {{"vi": ["...", "..."], "en": ["...", "..."]}},
  "grammar_tip": {{"vi": "...", "en": "..."}}
}}

Requirements:
- conversation_context: Summarize what has been discussed (1 sentence)
- turn_goal: What the learner should accomplish in their next turn (1 sentence)
- suggested_approach: How to respond (1-2 sentences)
- example_phrases: 2-3 example sentences the learner could say
- grammar_tip: Relevant grammar point for this level (1 sentence)

Return ONLY the JSON object, no other text."""

        return prompt

    def _call_bedrock(self, prompt: str) -> tuple[dict, int, int]:
        """Call Bedrock and parse JSON response.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Tuple of (parsed_json_dict, input_tokens, output_tokens)
            
        Raises:
            Exception: If Bedrock call fails or JSON parsing fails
        """
        try:
            # Call Bedrock with Amazon Nova Micro
            response = self._bedrock.invoke_model(
                modelId="apac.amazon.nova-micro-v1:0",
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    "max_tokens": 300,
                    "temperature": 0.7,
                }),
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            content_text = response_body["content"][0]["text"].strip()
            
            # Extract token usage (AWS Nova format)
            usage = response_body.get("usage", {})
            input_tokens = usage.get("inputTokens", 0)
            output_tokens = usage.get("outputTokens", 0)
            
            # Parse JSON from content
            hint_data = json.loads(content_text)
            
            return hint_data, input_tokens, output_tokens
            
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON from Bedrock response",
                extra={
                    "error": str(e),
                    "model_id": "apac.amazon.nova-micro-v1:0",
                }
            )
            raise
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            # Handle AWS Nova specific errors per AWS docs
            if error_code == "ValidationException":
                if "responsible AI" in error_message.lower() or "content policy" in error_message.lower():
                    logger.warning(
                        "Bedrock content blocked by Responsible AI policy",
                        extra={
                            "error_code": error_code,
                            "error_message": error_message,
                            "model_id": "apac.amazon.nova-micro-v1:0",
                        }
                    )
                else:
                    logger.error(
                        "Bedrock input validation error",
                        extra={
                            "error_code": error_code,
                            "error_message": error_message,
                            "model_id": "apac.amazon.nova-micro-v1:0",
                        }
                    )
            else:
                logger.error(
                    "Bedrock API call failed for structured hint",
                    extra={
                        "error_code": error_code,
                        "error_message": error_message,
                        "model_id": "apac.amazon.nova-micro-v1:0",
                    }
                )
            raise
