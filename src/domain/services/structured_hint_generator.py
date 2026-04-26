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
            # Build prompt with context
            prompt = self._build_prompt(session, last_ai_turn, turn_history)
            
            # Call Bedrock with retry logic (Fix #4)
            hint_data, input_tokens, output_tokens = self._call_bedrock_with_retry(prompt)
            
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

        prompt = f"""Bạn là giáo viên tiếng Anh tạo gợi ý tự nhiên để giúp học viên Việt Nam không bị mất phương hướng.

Chủ đề: {session.scenario_title or 'Conversation'}
Mục tiêu: {current_goal}
Trình độ: {level_str}
AI vừa nói: "{last_ai_content}"

NHIỆM VỤ: Tạo gợi ý tự nhiên (kiểu chain-of-hints) để:
1. Giúp học viên hiểu AI đang hỏi/nói gì
2. Hướng dẫn suy nghĩ về chủ đề (không cho đáp án)
3. Gợi ý hướng trả lời + ví dụ mẫu (để học viên có ý tưởng)
4. Thêm tip nhỏ hoặc icon để gợi ý tự nhiên

Gợi ý nên:
- Bắt đầu bằng "Chào bạn," để tự nhiên
- Dẫn dắt ngữ cảnh (AI đang hỏi gì)
- Đưa ra 2-3 ví dụ mẫu cụ thể (bullet, in đậm)
- Kết thúc bằng tip với icon 💡 + **bold** cấu trúc/từ vựng chính
- Ngắn gọn (3-5 câu)
- Tự nhiên, không giáo điều

Trả về JSON (SONG NGỮ):

{{
  "level": "{level_str}",
  "type": "hint",
  "markdown_vi": "Gợi ý tự nhiên bằng tiếng Việt (3-4 câu, có ví dụ mẫu)",
  "markdown_en": "Natural hint in English (3-4 sentences, with examples)"
}}

Ví dụ:
AI hỏi: "What do you usually do in the morning?"
{{
  "markdown_vi": "Chào bạn, AI đang hỏi về thói quen sáng của bạn. Hãy kể về những hoạt động từ lúc thức dậy đến khi đi làm/học.\\n- **'I wake up at 6 AM, have breakfast, take a shower, and then go to work'**\\n- **'I usually wake up late, drink coffee, and rush to school'**\\n- **'I wake up, exercise, shower, and have breakfast before work'**\\n\\n💡 Bạn có thể dùng **thì hiện tại đơn** (I wake up, I have) để nói về thói quen hàng ngày.",
  "markdown_en": "Hi there, AI is asking about your morning routine. Tell about what you do from waking up to going to work/school.\\n- **'I wake up at 6 AM, have breakfast, take a shower, and then go to work'**\\n- **'I usually wake up late, drink coffee, and rush to school'**\\n- **'I wake up, exercise, shower, and have breakfast before work'**\\n\\n💡 You can use **simple present tense** (I wake up, I have) to talk about daily habits."
}}

Ví dụ khác:
AI hỏi: "Tell me about your favorite hobby"
{{
  "markdown_vi": "Chào bạn, AI muốn biết sở thích của bạn. Chọn một hoạt động bạn thích và kể về nó.\\n- **'My favorite hobby is reading. I read novels every evening'**\\n- **'I love playing basketball because it keeps me healthy and I enjoy playing with my friends'**\\n- **'I enjoy cooking because I can create new dishes and share them with family'**\\n\\n💡 Bạn có thể nói **tại sao** bạn thích nó (vì sao, lợi ích gì) để câu trả lời hoàn chỉnh hơn.",
  "markdown_en": "Hi there, AI wants to know about your favorite hobby. Pick an activity you enjoy and tell about it.\\n- **'My favorite hobby is reading. I read novels every evening'**\\n- **'I love playing basketball because it keeps me healthy and I enjoy playing with my friends'**\\n- **'I enjoy cooking because I can create new dishes and share them with family'**\\n\\n💡 You can explain **why** you like it (benefits, reasons) to make your answer more complete."
}}

Ví dụ thứ ba:
AI hỏi: "Where did you go last weekend?"
{{
  "markdown_vi": "Chào bạn, AI muốn biết bạn đi đâu cuối tuần trước. Kể về một nơi bạn đã đi.\\n- **'I went to the beach with my family'**\\n- **'I stayed home and watched movies'**\\n- **'I visited my grandparents in the countryside'**\\n\\n💡 Bạn có thể dùng **thì quá khứ đơn** (went, stayed, visited) vì nó đã xảy ra rồi.",
  "markdown_en": "Hi there, AI wants to know where you went last weekend. Tell about a place you visited.\\n- **'I went to the beach with my family'**\\n- **'I stayed home and watched movies'**\\n- **'I visited my grandparents in the countryside'**\\n\\n💡 You can use **past simple tense** (went, stayed, visited) because it already happened."
}}

QUAN TRỌNG: Trả về JSON với newline thực sự (\\n), không phải escaped string. Ví dụ:
- ĐÚNG: "Chào bạn,\\n- **'example'**\\n\\n💡 Tip"
- SAI: "Chào bạn,\\\\n- **'example'**\\\\n\\\\n💡 Tip"

Chỉ trả về JSON, không có text khác."""

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
        
        for attempt in range(max_retries + 1):
            try:
                return self._call_bedrock(prompt)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                
                # Retry on transient errors
                if error_code in ["ThrottlingException", "ServiceUnavailableException", "InternalServerException"]:
                    if attempt < max_retries:
                        backoff = 2 ** attempt  # Exponential backoff: 1s, 2s
                        logger.warning(
                            f"Bedrock call failed with {error_code}, retrying in {backoff}s (attempt {attempt + 1}/{max_retries + 1})",
                            extra={
                                "error_code": error_code,
                                "attempt": attempt + 1,
                                "max_retries": max_retries + 1,
                                "backoff_seconds": backoff,
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
                modelId="apac.amazon.nova-micro-v1:0",
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}],
                        }
                    ],
                    "inferenceConfig": {
                        "maxTokens": 1000,
                        "temperature": 0.7,
                    },
                }),
            )
            
            # Collect streamed response
            content_text = ""
            input_tokens = 0
            output_tokens = 0
            
            for event in response["body"]:
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
            hint_data = json.loads(content_text.strip())
            
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
