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
            # Build system and user prompts (AWS best practice: separate roles)
            prompt_start = time.time()
            system_prompt = self._build_system_prompt(session)
            user_prompt = self._build_user_prompt(session, last_ai_turn, turn_history)
            prompt_time = (time.time() - prompt_start) * 1000
            
            # Call Bedrock with retry logic (Fix #4)
            bedrock_start = time.time()
            hint_data, input_tokens, output_tokens = self._call_bedrock_with_retry(system_prompt, user_prompt)
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

    def _build_system_prompt(self, session: Any) -> str:
        """Build system prompt (behavioral parameters).
        
        AWS best practice: System role establishes overall behavioral parameters.
        Reference: https://docs.aws.amazon.com/nova/latest/userguide/prompting-text-understanding.html
        """
        return """You are an English teacher creating natural, conversational hints for Vietnamese learners.

Your role:
- Explain context in Vietnamese (so learner understands)
- Provide examples in English (so learner learns correctly)
- NEVER translate English examples to Vietnamese
- Use markdown formatting: bullet points for examples, bold for key phrases
- Keep natural and conversational tone

Output format: Return ONLY valid JSON with these fields:
- level: CEFR level (A1, A2, B1, B2, C1, C2)
- type: "hint"
- markdown_vi: Vietnamese explanation with English examples
- markdown_en: English explanation with English examples"""

    def _build_user_prompt(
        self,
        session: Any,
        last_ai_turn: Optional[Any],
        turn_history: list[Any],
    ) -> str:
        """Build user prompt (context + task + few-shot examples).
        
        AWS best practice: Few-shot prompting with diverse examples improves accuracy.
        Reference: https://docs.aws.amazon.com/nova/latest/userguide/prompting-examples.html
        """
        last_ai_content = last_ai_turn.content if last_ai_turn else "Let's start the conversation!"
        import re
        last_ai_content = re.sub(r"^\[[^\]]+\]\s*", "", last_ai_content).strip()

        current_goal = session.selected_goal if hasattr(session, 'selected_goal') and session.selected_goal else "general conversation"
        level_str = session.level.value if hasattr(session.level, "value") else str(session.level)
        ai_character = session.ai_character if hasattr(session, 'ai_character') else "Sarah"

        # Few-shot examples (diverse: basic question, follow-up, complex scenario)
        examples = [
            {
                "input": 'AI: "What do you usually do in the morning?" | Level: A1',
                "output": """{
  "level": "A1",
  "type": "hint",
  "markdown_vi": "Sarah muốn biết thói quen sáng của bạn. Hãy kể về những hoạt động từ lúc thức dậy đến khi đi làm/học.\\n\\n- I wake up at 6 AM, have breakfast, take a shower, and then go to work\\n- I usually wake up late, drink coffee, and rush to school\\n\\n💡 Dùng simple present tense (I wake up, I have, I go) để nói về thói quen hàng ngày.",
  "markdown_en": "Sarah is asking about your morning routine. Tell what you do from waking up to going to work/school.\\n\\n- I wake up at 6 AM, have breakfast, take a shower, and then go to work\\n- I usually wake up late, drink coffee, and rush to school\\n\\n💡 Use simple present tense (I wake up, I have, I go) for daily habits."
}"""
            },
            {
                "input": 'AI: "What did you do last weekend?" | Level: B1',
                "output": """{
  "level": "B1",
  "type": "hint",
  "markdown_vi": "Sarah muốn biết bạn đã làm gì vào cuối tuần vừa rồi. Kể lại các hoạt động đã xảy ra.\\n\\n- I went to the beach with my friends and we had a great time\\n- I stayed home, watched movies, and relaxed\\n\\n💡 Dùng past simple (went, stayed, watched) để kể chuyện đã xảy ra. Dùng 'and' để nối các hành động.",
  "markdown_en": "Sarah is asking what you did last weekend. Tell her about activities that happened.\\n\\n- I went to the beach with my friends and we had a great time\\n- I stayed home, watched movies, and relaxed\\n\\n💡 Use past simple (went, stayed, watched) for completed actions. Use 'and' to connect actions."
}"""
            }
        ]

        prompt = f"""CONTEXT:
- Scenario: {session.scenario_title or 'Conversation'}
- Goal: {current_goal}
- Level: {level_str}
- AI Character: {ai_character}
- AI just said: "{last_ai_content}"

TASK: Create a natural hint for this learner.

EXAMPLES (few-shot):
Example 1: {examples[0]['input']}
Output: {examples[0]['output']}

Example 2: {examples[1]['input']}
Output: {examples[1]['output']}

NOW, create a hint for:
AI: "{last_ai_content}" | Level: {level_str}

Return ONLY the JSON object (no preamble, no markdown wrapper)."""

        return prompt

    def _call_bedrock_with_retry(self, system_prompt: str, user_prompt: str, max_retries: int = 2) -> tuple[dict, int, int]:
        """Call Bedrock with retry logic for transient errors (Fix #4).
        
        Args:
            system_prompt: System role prompt (behavioral parameters)
            user_prompt: User role prompt (context + task + examples)
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
                return self._call_bedrock(system_prompt, user_prompt)
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

    def _call_bedrock(self, system_prompt: str, user_prompt: str) -> tuple[dict, int, int]:
        """Call Bedrock with streaming and parse JSON response.
        
        Uses Nova's structured output with tool config for guaranteed JSON compliance.
        Reference: https://docs.aws.amazon.com/nova/latest/userguide/concept-chapter-servicename.html
        
        Args:
            system_prompt: System role prompt (behavioral parameters)
            user_prompt: User role prompt (context + task + examples)
            
        Returns:
            Tuple of (parsed_json_dict, input_tokens, output_tokens)
            
        Raises:
            Exception: If Bedrock call fails or JSON parsing fails
        """
        try:
            # Define JSON schema for structured output (Nova best practice)
            # Constrained decoding ensures valid JSON output
            tool_config = {
                "tools": [
                    {
                        "toolSpec": {
                            "name": "StructuredHint",
                            "description": "Generate a structured bilingual hint for English learners",
                            "inputSchema": {
                                "json": {
                                    "type": "object",
                                    "properties": {
                                        "level": {
                                            "type": "string",
                                            "description": "CEFR level (A1, A2, B1, B2, C1, C2)"
                                        },
                                        "type": {
                                            "type": "string",
                                            "description": "Hint type (hint, vocabulary_suggestion, strategic_guidance, metacognitive_prompt)"
                                        },
                                        "markdown_vi": {
                                            "type": "string",
                                            "description": "Full hint in Vietnamese with English examples (markdown format)"
                                        },
                                        "markdown_en": {
                                            "type": "string",
                                            "description": "Full hint in English with English examples (markdown format)"
                                        }
                                    },
                                    "required": ["level", "type", "markdown_vi", "markdown_en"]
                                }
                            }
                        }
                    }
                ],
                "toolChoice": {
                    "tool": {
                        "name": "StructuredHint"
                    }
                }
            }
            
            # Amazon Nova format with streaming + structured output
            # Reference: https://docs.aws.amazon.com/nova/latest/userguide/concept-chapter-servicename.html
            # AWS best practices:
            # - temperature=0 for structured output (greedy decoding)
            # - performanceConfig.latency="optimized" for 20-30% latency reduction
            response = self._bedrock.converse_stream(
                modelId="apac.amazon.nova-lite-v1:0",
                system=[{"text": system_prompt}],
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": user_prompt}],
                    }
                ],
                toolConfig=tool_config,
                inferenceConfig={
                    "maxTokens": 500,
                    "temperature": 0,
                },
                performanceConfig={
                    "latency": "optimized"  # AWS best practice: 20-30% latency reduction
                },
            )
            
            # Collect streamed response with timeout
            content_text = ""
            input_tokens = 0
            output_tokens = 0
            chunk_count = 0
            max_chunks = 100  # Safety limit to prevent infinite loops
            tool_use_data = None
            
            for event in response["stream"]:
                chunk_count += 1
                if chunk_count > max_chunks:
                    logger.warning(f"Bedrock response exceeded {max_chunks} chunks, truncating")
                    break
                
                # Handle tool use (structured output)
                if "contentBlockStart" in event:
                    start = event["contentBlockStart"]
                    if "toolUse" in start.get("start", {}):
                        tool_use_data = start["start"]["toolUse"]
                
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"].get("delta", {})
                    if "toolUse" in delta:
                        # Accumulate tool input
                        if tool_use_data is None:
                            tool_use_data = {}
                        if "input" not in tool_use_data:
                            tool_use_data["input"] = ""
                        tool_use_data["input"] += delta["toolUse"].get("input", "")
                
                # Extract token usage from metadata
                if "metadata" in event:
                    usage = event["metadata"].get("usage", {})
                    input_tokens = usage.get("inputTokens", input_tokens)
                    output_tokens = usage.get("outputTokens", output_tokens)
            
            # Parse tool use input as JSON
            if tool_use_data and "input" in tool_use_data:
                hint_data = json.loads(tool_use_data["input"])
            else:
                raise ValueError("No tool use data received from Bedrock")
            
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
