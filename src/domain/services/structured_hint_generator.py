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
            
            # Call Bedrock (AWS SDK handles retry with exponential backoff + jitter)
            bedrock_start = time.time()
            hint_data, input_tokens, output_tokens = self._call_bedrock(system_prompt, user_prompt)
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
        """Build system prompt for hint generation.

        Reference: https://docs.aws.amazon.com/nova/latest/userguide/prompting-system-role.html
        """
        learner_role = getattr(session, 'learner_role_id', 'learner')
        ai_role = getattr(session, 'ai_role_id', 'conversation partner')
        
        return f"""You are a friendly English teacher helping Vietnamese learners practice conversation.

IMPORTANT: The learner is playing the role of "{learner_role}" and the AI is playing "{ai_role}".

When the AI says something, create a helpful hint so the learner knows how to respond naturally in English FROM THEIR ROLE as "{learner_role}".

Give 2-3 natural English example sentences they can use or adapt AS A "{learner_role}", plus one short grammar tip in Vietnamese. Keep it concise and encouraging.

Output format: Return ONLY valid JSON with these exact fields:
- level: CEFR level string
- type: "hint"
- markdown_vi: hint in Vietnamese with English examples (markdown)
- markdown_en: hint in English with English examples (markdown)"""

    def _build_user_prompt(
        self,
        session: Any,
        last_ai_turn: Optional[Any],
        turn_history: list[Any],
    ) -> str:
        """Build user prompt with context and few-shot examples.

        Reference: https://docs.aws.amazon.com/nova/latest/userguide/prompting-examples.html
        """
        last_ai_content = last_ai_turn.content if last_ai_turn else "Let's start the conversation!"
        import re
        last_ai_content = re.sub(r"^\[[^\]]+\]\s*", "", last_ai_content).strip()

        current_goal = session.selected_goal if hasattr(session, 'selected_goal') and session.selected_goal else "general conversation"
        level_str = session.level.value if hasattr(session.level, "value") else str(session.level)
        ai_character = session.ai_character if hasattr(session, 'ai_character') else "Sarah"
        learner_role = getattr(session, 'learner_role_id', 'learner')
        ai_role = getattr(session, 'ai_role_id', 'conversation partner')

        # 3 diverse few-shot examples (A1, B1, C1) — AWS best practice
        # Examples show role-aware hints (learner as customer, AI as waiter)
        examples = [
            {
                "context": 'Level: A1 | Learner Role: customer | AI Role: waiter | AI said: "What would you like to order?"',
                "output": """{
  "level": "A1",
  "type": "hint",
  "markdown_vi": "Người phục vụ hỏi bạn muốn gọi món gì. Hãy nói món ăn/đồ uống bạn muốn.\\n\\n- **I'd like** a coffee and a sandwich, please\\n- **Can I have** the chicken salad?\\n\\n💡 Dùng **I'd like** hoặc **Can I have** khi gọi món lịch sự.",
  "markdown_en": "The waiter is asking what you want to order. Tell them your food/drink choice.\\n\\n- **I'd like** a coffee and a sandwich, please\\n- **Can I have** the chicken salad?\\n\\n💡 Use **I'd like** or **Can I have** to order politely."
}"""
            },
            {
                "context": 'Level: B1 | Learner Role: customer | AI Role: waiter | AI said: "Would you like anything else with that?"',
                "output": """{
  "level": "B1",
  "type": "hint",
  "markdown_vi": "Người phục vụ hỏi bạn có muốn thêm gì không. Bạn có thể gọi thêm hoặc từ chối lịch sự.\\n\\n- **That's all for now**, thank you\\n- **Could I also get** a side of fries with that?\\n\\n💡 Dùng **That's all** để kết thúc order, hoặc **Could I also get** để gọi thêm.",
  "markdown_en": "The waiter is asking if you want anything else. You can add more or politely decline.\\n\\n- **That's all for now**, thank you\\n- **Could I also get** a side of fries with that?\\n\\n💡 Use **That's all** to finish ordering, or **Could I also get** to add more."
}"""
            },
            {
                "context": 'Level: C1 | Learner Role: job applicant | AI Role: interviewer | AI said: "How would you describe your ideal workplace?"',
                "output": """{
  "level": "C1",
  "type": "hint",
  "markdown_vi": "Người phỏng vấn hỏi bạn (ứng viên) về môi trường làm việc lý tưởng. Mô tả văn hóa, cơ hội phát triển, và sự cân bằng công việc-cuộc sống từ góc độ ứng viên.\\n\\n- My ideal workplace **would foster** innovation while **maintaining** a collaborative atmosphere where I can **contribute meaningfully**\\n- I **envision** an environment that **prioritizes** professional development and work-life balance\\n\\n💡 Dùng **conditional** (would foster, would prioritize) và từ vựng nâng cao để thể hiện trình độ C1. Nhấn mạnh giá trị bạn mang lại.",
  "markdown_en": "The interviewer is asking you (as a job applicant) about your ideal workplace. Describe culture, growth opportunities, and work-life balance from a candidate's perspective.\\n\\n- My ideal workplace **would foster** innovation while **maintaining** a collaborative atmosphere where I can **contribute meaningfully**\\n- I **envision** an environment that **prioritizes** professional development and work-life balance\\n\\n💡 Use **conditional** (would foster, would prioritize) and sophisticated vocabulary for C1 level. Emphasize the value you bring."
}"""
            }
        ]

        return f"""CONTEXT:
- Scenario: {getattr(session, 'scenario_title', 'Conversation')}
- Goal: {current_goal}
- Level: {level_str}
- Learner Role: {learner_role}
- AI Role: {ai_role}
- AI Character: {ai_character}
- AI just said: "{last_ai_content}"

EXAMPLES:
Input: {examples[0]['context']}
Output: {examples[0]['output']}

Input: {examples[1]['context']}
Output: {examples[1]['output']}

Input: {examples[2]['context']}
Output: {examples[2]['output']}

NOW create a hint for:
Input: Level: {level_str} | Learner Role: {learner_role} | AI Role: {ai_role} | AI said: "{last_ai_content}"
Output:"""

    def _call_bedrock(self, system_prompt: str, user_prompt: str) -> tuple[dict, int, int]:
        """Call Bedrock with streaming and parse JSON response.
        
        Uses Nova's structured output with tool config for guaranteed JSON compliance.
        AWS SDK automatically retries with exponential backoff + jitter (max 3 attempts).
        
        Reference: https://docs.aws.amazon.com/nova/latest/userguide/concept-chapter-servicename.html
        
        Args:
            system_prompt: System role prompt (behavioral parameters)
            user_prompt: User role prompt (context + task + examples)
            
        Returns:
            Tuple of (parsed_json_dict, input_tokens, output_tokens)
            
        Raises:
            Exception: If Bedrock call fails after all retries or JSON parsing fails
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
            
            # Amazon Nova format with NON-streaming + structured output
            # Fix: converse_stream with toolConfig has issues, use converse instead
            # Reference: https://docs.aws.amazon.com/nova/latest/userguide/concept-chapter-servicename.html
            response = self._bedrock.converse(
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
            )
            
            # Extract tool use from response
            input_tokens = response.get("usage", {}).get("inputTokens", 0)
            output_tokens = response.get("usage", {}).get("outputTokens", 0)
            
            # Find tool use in output
            tool_use_data = None
            for content_block in response.get("output", {}).get("message", {}).get("content", []):
                if "toolUse" in content_block:
                    tool_use_data = content_block["toolUse"]
                    break
            
            # Parse tool use input as JSON
            if tool_use_data and "input" in tool_use_data:
                hint_data = tool_use_data["input"]
            else:
                raise ValueError("No tool use data received from Bedrock")
            
            # Validate response structure and content
            is_valid = validate_structured_hint(hint_data)
            if not is_valid:
                logger.warning(
                    "Hint response validation failed but continuing with response",
                    extra={
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
