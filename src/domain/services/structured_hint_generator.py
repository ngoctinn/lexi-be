"""Bilingual hint generation for conversation sessions (all CEFR levels).

Level-specific scaffolding strategies (based on SLA research + Duolingo patterns):
- A1-A2: Procedural — key vocabulary + 2-3 ready-to-use example sentences
- B1-B2: Strategic — sentence structure guidance + grammar tip + examples to adapt
- C1-C2: Metacognitive — nuance/register analysis + advanced alternatives

Output: markdown_vi + markdown_en strings (frontend renders markdown).
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from botocore.exceptions import ClientError
from domain.services.prompt_validator import validate_structured_hint_response, log_validation_errors

logger = logging.getLogger(__name__)


@dataclass
class StructuredHint:
    """Bilingual markdown hint for learners (all CEFR levels).

    Fields:
        level: CEFR level (A1–C2)
        type: vocabulary_suggestion | strategic_guidance | metacognitive_prompt
        markdown_vi: Full hint in Vietnamese, formatted as markdown
        markdown_en: Full hint in English, formatted as markdown

    Markdown sections vary by level:
        A1/A2: 💬 Tình huống | 📝 Từ khoá | ✅ Câu mẫu | 💡 Mẹo ngữ pháp
        B1/B2: 💬 Tình huống | 🎯 Gợi ý | ✅ Câu mẫu | 💡 Ngữ pháp
        C1/C2: 💬 Tình huống | 🎯 Phân tích | ✅ Lựa chọn nâng cao | 💡 Phong cách
    """
    level: str
    type: str
    markdown_vi: str
    markdown_en: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "markdown": {
                "vi": self.markdown_vi,
                "en": self.markdown_en,
            },
        }


def validate_structured_hint(hint: dict) -> bool:
    """Validate structured hint has required fields."""
    required = ["level", "type", "markdown_vi", "markdown_en"]
    for field in required:
        if field not in hint:
            return False
    if not isinstance(hint["markdown_vi"], str) or not hint["markdown_vi"].strip():
        return False
    if not isinstance(hint["markdown_en"], str) or not hint["markdown_en"].strip():
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
            prompt_start = time.time()
            prompt = self._build_prompt(session, last_ai_turn, turn_history)
            prompt_time = (time.time() - prompt_start) * 1000
            
            # Call Bedrock with retry logic (Fix #4)
            bedrock_start = time.time()
            hint_data, input_tokens, output_tokens = self._call_bedrock_with_retry(prompt)
            bedrock_time = (time.time() - bedrock_start) * 1000
            
            # Validate response
            if not validate_structured_hint(hint_data):
                raise ValueError("Invalid structured hint response from Bedrock")
            
            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            
            # Estimate cost (Amazon Nova Lite pricing)
            cost_usd = (input_tokens / 1000 * 0.00006) + (output_tokens / 1000 * 0.00024)
            
            # Log performance metrics
            logger.info(
                "Structured hint generated successfully",
                extra={
                    "session_id": session_id,
                    "turn_index": turn_index,
                    "latency_ms": round(latency_ms, 2),
                    "prompt_time_ms": round(prompt_time, 2),
                    "bedrock_time_ms": round(bedrock_time, 2),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": round(cost_usd, 6),
                }
            )
            
            # Return StructuredHint dataclass
            return StructuredHint(
                level=hint_data["level"],
                type=hint_data["type"],
                markdown_vi=hint_data["markdown_vi"],
                markdown_en=hint_data["markdown_en"],
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
        """Build prompt for natural, conversational hints (chain-of-hints approach).
        
        Based on research: "Designing and Evaluating Chain-of-Hints for Scientific Question Answering"
        - Hints should scaffold learner toward understanding, not give away answer
        - Natural language flow, not rigid sections
        - Focus on guiding thinking, not providing solutions
        """
        last_ai_content = last_ai_turn.content if last_ai_turn else "Let's start the conversation!"
        # Strip delivery cue from AI content if present
        import re
        last_ai_content = re.sub(r"^\[[^\]]+\]\s*", "", last_ai_content).strip()

        current_goal = session.selected_goal if hasattr(session, 'selected_goal') and session.selected_goal else "general conversation"
        level_str = session.level.value if hasattr(session.level, "value") else str(session.level)
        ai_character = session.ai_character if hasattr(session, 'ai_character') else "Sarah"

        prompt = f"""You are an English teacher creating natural, conversational hints for Vietnamese learners.

CONTEXT:
- Scenario: {session.scenario_title or 'Conversation'}
- Goal: {current_goal}
- Level: {level_str}
- AI Character: {ai_character}
- AI just said: "{last_ai_content}"

CRITICAL RULES:
1. EXPLANATION in Vietnamese (learner understands context)
2. EXAMPLES ALWAYS in English (learner learns correct English)
3. NEVER translate English examples to Vietnamese
4. Use markdown with bullet points and bold text
5. Keep it natural and conversational

TASK: Create a natural hint:
1. Start with "{ai_character} wants to know..." or "{ai_character} is asking..."
2. Explain context in Vietnamese (2-3 sentences)
3. Provide 2-3 example sentences in English (bullet points, bold)
4. End with 💡 tip in Vietnamese explaining grammar/vocabulary
5. Total: 3-5 sentences + examples

RETURN ONLY JSON (no other text):
{{
  "level": "{level_str}",
  "type": "hint",
  "markdown_vi": "Vietnamese explanation with English examples",
  "markdown_en": "English explanation with English examples"
}}

CORRECT EXAMPLE:
AI said: "What do you usually do in the morning?"
Character: Sarah
{{
  "markdown_vi": "Sarah muốn biết thói quen sáng của bạn. Hãy kể về những hoạt động từ lúc thức dậy đến khi đi làm/học.
- **I wake up at 6 AM, have breakfast, take a shower, and then go to work**
- **I usually wake up late, drink coffee, and rush to school**

💡 Dùng **simple present tense** (I wake up, I have, I go) để nói về thói quen hàng ngày.",
  "markdown_en": "Sarah is asking about your morning routine. Tell what you do from waking up to going to work/school.
- **I wake up at 6 AM, have breakfast, take a shower, and then go to work**
- **I usually wake up late, drink coffee, and rush to school**

💡 Use **simple present tense** (I wake up, I have, I go) for daily habits."
}}

REMEMBER: Vietnamese explanation + English examples = effective learning."""

        return prompt

    def _call_bedrock_with_retry(self, prompt: str, max_retries: int = 2) -> tuple[dict, int, int]:
        """Call Bedrock with retry logic for transient errors (Fix #4).
        
        Args:
            prompt: Prompt string
            max_retries: Maximum number of retries (default: 2)
            
        Returns:
            Tuple of (parsed_json_dict, input_tokens, output_tokens)
            
        Raises:
            Exception: If all retries fail or permanent error occurs
        """
        import time
        import random
        
        for attempt in range(max_retries + 1):
            try:
                return self._call_bedrock(prompt)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                
                # Retry on transient errors
                if error_code in ["ThrottlingException", "ServiceUnavailableException", "InternalServerException"]:
                    if attempt < max_retries:
                        # Exponential backoff with jitter: (2^attempt) + random(0-1)
                        base_backoff = 2 ** attempt
                        jitter = random.uniform(0, 1)
                        backoff = base_backoff + jitter
                        logger.warning(
                            f"Bedrock call failed with {error_code}, retrying in {backoff:.2f}s (attempt {attempt + 1}/{max_retries + 1})",
                            extra={
                                "error_code": error_code,
                                "attempt": attempt + 1,
                                "max_retries": max_retries + 1,
                                "backoff_seconds": round(backoff, 2),
                            }
                        )
                        time.sleep(backoff)
                        continue
                
                # Don't retry on permanent errors
                raise
            except Exception as e:
                # Don't retry on non-ClientError exceptions
                raise

    def _call_bedrock(self, prompt: str) -> tuple[dict, int, int]:
        """Call Bedrock with streaming and parse JSON response.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Tuple of (parsed_json_dict, input_tokens, output_tokens)
            
        Raises:
            Exception: If Bedrock call fails or JSON parsing fails
        """
        try:
            # Amazon Nova format with streaming
            # Reference: https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html
            response = self._bedrock.invoke_model_with_response_stream(
                modelId="apac.amazon.nova-lite-v1:0",
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}],
                        }
                    ],
                    "inferenceConfig": {
                        "maxTokens": 500,  # Reduced from 1000 (hints don't need that much)
                        "temperature": 0.7,
                    },
                }),
            )
            
            # Collect streamed response with timeout
            content_text = ""
            input_tokens = 0
            output_tokens = 0
            chunk_count = 0
            max_chunks = 100  # Safety limit to prevent infinite loops
            
            for event in response["body"]:
                chunk_count += 1
                if chunk_count > max_chunks:
                    logger.warning(f"Bedrock response exceeded {max_chunks} chunks, truncating")
                    break
                    
                if "chunk" in event:
                    chunk = json.loads(event["chunk"]["bytes"].decode())
                    
                    # Extract content delta
                    if "contentBlockDelta" in chunk:
                        delta = chunk["contentBlockDelta"].get("delta", {})
                        if "text" in delta:
                            content_text += delta["text"]
                    
                    # Extract token usage from metadata
                    if "metadata" in chunk:
                        usage = chunk["metadata"].get("usage", {})
                        input_tokens = usage.get("inputTokens", input_tokens)
                        output_tokens = usage.get("outputTokens", output_tokens)
            
            # Parse JSON from collected content
            # Fix: Handle literal newlines in JSON strings by escaping them
            content_text = content_text.strip()
            # Replace unescaped newlines in the JSON string with escaped newlines
            # This handles cases where Bedrock returns actual newlines instead of \n
            import re
            # Find all string values and escape their newlines
            def escape_newlines_in_json(text):
                """Escape literal newlines in JSON string values."""
                try:
                    # Try parsing first - if it works, no need to fix
                    return json.loads(text)
                except json.JSONDecodeError as e:
                    if "Invalid control character" in str(e):
                        # Replace literal newlines with escaped newlines
                        # This is a bit hacky but necessary for Bedrock responses
                        text = text.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                        return json.loads(text)
                    raise
            
            hint_data = escape_newlines_in_json(content_text)
            
            # Validate response structure and content
            is_valid, validation_errors = validate_structured_hint_response(hint_data)
            if not is_valid:
                log_validation_errors(validation_errors, "structured_hint response")
                logger.warning(
                    "Hint response validation failed but continuing with response",
                    extra={
                        "error_count": len(validation_errors),
                        "model_id": "apac.amazon.nova-lite-v1:0",
                    }
                )
            
            return hint_data, input_tokens, output_tokens
            
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON from Bedrock response",
                extra={
                    "error": str(e),
                    "model_id": "apac.amazon.nova-lite-v1:0",
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
                            "model_id": "apac.amazon.nova-lite-v1:0",
                        }
                    )
                else:
                    logger.error(
                        "Bedrock input validation error",
                        extra={
                            "error_code": error_code,
                            "error_message": error_message,
                            "model_id": "apac.amazon.nova-lite-v1:0",
                        }
                    )
            else:
                logger.error(
                    "Bedrock API call failed for structured hint",
                    extra={
                        "error_code": error_code,
                        "error_message": error_message,
                        "model_id": "apac.amazon.nova-lite-v1:0",
                    }
                )
            raise
