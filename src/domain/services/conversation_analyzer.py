"""
Conversation Analyzer - Analyzes learner turns for formative assessment.

Provides turn-by-turn feedback with:
- Mistakes (⚠️): Grammar, vocabulary, or usage errors with formatting
- Improvements (💡): Suggestions for better expression
"""

import json
import logging
import time
from dataclasses import dataclass
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class TurnAnalysis:
    """Analysis result for a single turn."""

    markdown_vi: str  # Vietnamese markdown
    markdown_en: str  # English markdown
    strengths: list[str]
    mistakes: list[str]
    improvements: list[str]
    overall_assessment: str


class ConversationAnalyzer:
    """Analyzes learner conversation turns using LLM."""

    def __init__(self, bedrock_client=None):
        self.bedrock_client = bedrock_client
        self._model_id = "apac.amazon.nova-micro-v1:0"

    def analyze_turn(
        self,
        learner_message: str,
        ai_response: str,
        level: str,
        scenario_context: str,
    ) -> TurnAnalysis:
        if not self.bedrock_client:
            raise ValueError("bedrock_client is required")

        system_prompt = self._build_system_prompt(level, scenario_context)
        user_prompt = self._build_user_prompt(learner_message, ai_response, level)

        # Retry logic for transient Bedrock errors
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                request_body = json.dumps({
                    "system": [{"text": system_prompt}],
                    "messages": [{"role": "user", "content": [{"text": user_prompt}]}],
                    "inferenceConfig": {
                        "maxTokens": 500,
                        "temperature": 0.3,
                    },
                })

                # Use streaming for better UX
                response = self.bedrock_client.invoke_model_with_response_stream(
                    modelId=self._model_id,
                    body=request_body,
                )

                # Collect streamed response
                analysis_text = ""
                input_tokens = 0
                output_tokens = 0
                
                for event in response["body"]:
                    if "chunk" in event:
                        chunk = json.loads(event["chunk"]["bytes"].decode())
                        
                        # Extract content delta
                        if "contentBlockDelta" in chunk:
                            delta = chunk["contentBlockDelta"].get("delta", {})
                            if "text" in delta:
                                analysis_text += delta["text"]
                        
                        # Extract token usage from metadata
                        if "metadata" in chunk:
                            usage = chunk["metadata"].get("usage", {})
                            input_tokens = usage.get("inputTokens", input_tokens)
                            output_tokens = usage.get("outputTokens", output_tokens)

                data = json.loads(analysis_text)

                # Extract bilingual content from LLM
                mistakes_vi = data.get("mistakes_vi", [])
                mistakes_en = data.get("mistakes_en", [])
                improvements_vi = data.get("improvements_vi", [])
                improvements_en = data.get("improvements_en", [])

                # Format markdown with proper styling
                markdown_vi = self._format_markdown_vi(mistakes_vi, improvements_vi)
                markdown_en = self._format_markdown_en(mistakes_en, improvements_en)

                return TurnAnalysis(
                    markdown_vi=markdown_vi,
                    markdown_en=markdown_en,
                    strengths=[],
                    mistakes=mistakes_vi,
                    improvements=improvements_vi,
                    overall_assessment="",
                )

            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse analysis JSON (attempt {attempt + 1}/{max_retries + 1}): {e}",
                    extra={
                        "attempt": attempt + 1,
                        "max_retries": max_retries + 1,
                        "error_type": "json_decode_error",
                    }
                )
                # JSON errors are permanent, don't retry
                return self._fallback_analysis()

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                error_message = e.response.get("Error", {}).get("Message", str(e))

                # Retry on transient errors
                if error_code in ["ThrottlingException", "ServiceUnavailableException", "InternalServerException"]:
                    if attempt < max_retries:
                        backoff = 2 ** attempt  # Exponential backoff: 1s, 2s
                        logger.warning(
                            f"Bedrock transient error (attempt {attempt + 1}/{max_retries + 1}), retrying in {backoff}s",
                            extra={
                                "error_code": error_code,
                                "error_message": error_message,
                                "attempt": attempt + 1,
                                "max_retries": max_retries + 1,
                                "backoff_seconds": backoff,
                            }
                        )
                        time.sleep(backoff)
                        continue

                # Permanent errors or max retries exhausted
                logger.error(
                    f"Bedrock API error (attempt {attempt + 1}/{max_retries + 1}): {error_code}",
                    extra={
                        "error_code": error_code,
                        "error_message": error_message,
                        "attempt": attempt + 1,
                        "max_retries": max_retries + 1,
                    }
                )
                return self._fallback_analysis()

            except Exception as e:
                logger.exception(
                    f"Unexpected error during analysis (attempt {attempt + 1}/{max_retries + 1}): {e}",
                    extra={
                        "attempt": attempt + 1,
                        "max_retries": max_retries + 1,
                        "error_type": type(e).__name__,
                    }
                )
                return self._fallback_analysis()

    def _build_system_prompt(self, level: str, scenario_context: str) -> str:
        level_guidance = {
            "A1": "Tập trung vào lỗi cơ bản: từ vựng, thì động từ, cấu trúc câu đơn giản.",
            "A2": "Tập trung vào lỗi thường gặp: thì, giới từ, cấu trúc câu.",
            "B1": "Tập trung vào lỗi ảnh hưởng đến rõ ràng: thì, giới từ, từ nối.",
            "B2": "Tập trung vào lỗi về sự trôi chảy: từ vựng chính xác, cấu trúc phức tạp.",
            "C1": "Tập trung vào lỗi tinh tế: phong cách, sắc thái, cách diễn đạt.",
            "C2": "Tập trung vào lỗi về sự thuần thục: nuance, register, idiom.",
        }

        return f"""Bạn là giáo viên tiếng Anh phân tích lỗi của học viên Việt Nam.

Ngữ cảnh: {scenario_context}
Trình độ: {level}
Hướng dẫn: {level_guidance.get(level, level_guidance["B1"])}

Nhiệm vụ: Phân tích lỗi và gợi ý cải thiện BẰNG TIẾNG VIỆT.
- Mỗi lỗi: chỉ ra từ/cấu trúc sai, giải thích tại sao sai
- Mỗi gợi ý: đưa ra cách diễn đạt đúng, giải thích tại sao đúng hơn
- Tối đa 2-3 lỗi, 2-3 gợi ý
- Trả về ĐÚNG JSON, không có markdown bao ngoài"""

    def _build_user_prompt(self, learner_message: str, ai_response: str, level: str) -> str:
        return f"""Phân tích câu này:

**Học viên nói:** {learner_message}

**AI phản hồi:** {ai_response}

NHIỆM VỤ: Phản hồi theo phong cách NÓI CHUYỆN TỰ NHIÊN (như người với người):
1. Nếu có lỗi: Nói "Bạn nhầm lẫn..." hoặc "Bạn có thể sửa..." (thân thiện, không dùng label "Lỗi:")
2. Gợi ý cải thiện: "Bạn có thể nói..." hoặc "Thử nói..." (khuyến khích, không áp đặt)
3. Phong cách: Như đang chat với bạn bè, tự nhiên, thân thiện

Trả về JSON (SONG NGỮ - tiếng Việt + tiếng Anh):

QUY TẮC FORMAT:
- KHÔNG thêm icon 💡 hoặc ⚠️ vào text (hệ thống tự động thêm)
- KHÔNG dùng label "Lỗi:" hay "Mistake:" - nói tự nhiên như người với người
- Giữ NGUYÊN câu tiếng Anh và in đậm **text** trong phần tiếng Việt
- Dùng ~~text~~ để gạch ngang phần sai
- Dẫn dắt như đang giải thích cho bạn bè

FORMAT CHO LỖI (mistakes) - Phong cách tự nhiên:
"Bạn nhầm lẫn chút ở ~~[phần sai]~~, nên sửa thành **[phần đúng]**\n\nVì [giải thích thân thiện, xuống dòng để dễ đọc]"
hoặc
"Ở đây bạn dùng ~~[sai]~~ nhưng nên dùng **[đúng]**\n\nVì [giải thích]"

FORMAT CHO GỢI Ý (improvements) - Phong cách khuyến khích:
"Bạn có thể nói **[Câu hay hơn]**\n\nĐể [lý do] nghe tự nhiên hơn"
hoặc
"Thử nói **[Câu hay hơn]**\n\nSẽ [lý do] và nghe pro hơn nha"

Nếu CÓ LỖI:
{{
  "mistakes_vi": ["Bạn nhầm lẫn chút ở ~~[sai]~~, nên sửa thành **[đúng]**\\n\\nVì [giải thích thân thiện]"],
  "mistakes_en": ["You mixed up ~~[wrong]~~ here, should be **[correct]**\\n\\nBecause [friendly explanation]"],
  "improvements_vi": ["Bạn có thể nói **[Câu hay hơn]**\\n\\nĐể [lý do] nghe tự nhiên hơn"],
  "improvements_en": ["You could say **[Better sentence]**\\n\\nTo [reason] sound more natural"]
}}

VÍ DỤ CỤ THỂ (phong cách nói chuyện tự nhiên):
{{
  "mistakes_vi": ["Bạn nhầm lẫn chút ở ~~go to school~~, nên sửa thành **went to school**\\n\\nVì khi có 'yesterday' (hôm qua) thì động từ phải ở dạng quá khứ nha. 'Go' là hiện tại, 'went' là quá khứ"],
  "mistakes_en": ["You mixed up ~~go to school~~ here, should be **went to school**\\n\\nBecause when you have 'yesterday', the verb needs to be in past tense. 'Go' is present, 'went' is past"],
  "improvements_vi": ["Bạn có thể nói **I went to school yesterday**\\n\\nĐể sắp xếp đúng trật tự từ. Trạng từ thời gian như 'yesterday' thường đứng cuối câu, nghe tự nhiên hơn"],
  "improvements_en": ["You could say **I went to school yesterday**\\n\\nTo follow correct word order. Time adverbs like 'yesterday' usually go at the end, sounds more natural"]
}}

VÍ DỤ KHÁC (không có lỗi, chỉ có gợi ý):
{{
  "improvements_vi": ["Thử nói **I really enjoy drinking coffee in the morning**\\n\\nSẽ phong phú hơn. 'Really enjoy' thể hiện cảm xúc mạnh hơn 'like', và thêm 'in the morning' cho cụ thể hơn"],
  "improvements_en": ["Try saying **I really enjoy drinking coffee in the morning**\\n\\nTo make it richer. 'Really enjoy' shows stronger feeling than 'like', and adding 'in the morning' gives more detail"]
}}

VÍ DỤ KHÁC (phong cách thân thiện):
{{
  "mistakes_vi": ["Ở đây bạn dùng ~~I go~~ nhưng nên dùng **I went**\\n\\nVì đang kể chuyện đã xảy ra rồi (quá khứ). Khi kể chuyện hôm qua, tuần trước thì dùng quá khứ nha"],
  "mistakes_en": ["Here you used ~~I go~~ but should use **I went**\\n\\nBecause you're talking about something that already happened (past). When telling stories about yesterday or last week, use past tense"],
  "improvements_vi": ["Bạn có thể thêm chi tiết như **I went to school yesterday and met my friends**\\n\\nĐể câu chuyện sinh động hơn. Thêm 'and met my friends' làm câu hay hơn"],
  "improvements_en": ["You could add details like **I went to school yesterday and met my friends**\\n\\nTo make the story more vivid. Adding 'and met my friends' makes it better"]
}}

Chỉ trả về JSON, không có text khác."""

    def _format_markdown_vi(self, mistakes: list[str], improvements: list[str]) -> str:
        sections = []

        if mistakes:
            for mistake in mistakes:
                sections.append(f"⚠️ {mistake}\n")
        
        if improvements:
            for improvement in improvements:
                sections.append(f"💡 {improvement}\n")

        return "".join(sections) if sections else "Không có phân tích nào."

    def _format_markdown_en(self, mistakes: list[str], improvements: list[str]) -> str:
        sections = []

        if mistakes:
            for mistake in mistakes:
                sections.append(f"⚠️ {mistake}\n")
        
        if improvements:
            for improvement in improvements:
                sections.append(f"💡 {improvement}\n")

        return "".join(sections) if sections else "No analysis available."

    def _fallback_analysis(self) -> TurnAnalysis:
        fallback_vi = "💡 Hệ thống phân tích đang gặp sự cố tạm thời. Vui lòng thử lại sau vài giây."
        fallback_en = "💡 Analysis system is temporarily unavailable. Please try again in a few seconds."

        return TurnAnalysis(
            markdown_vi=fallback_vi,
            markdown_en=fallback_en,
            strengths=[],
            mistakes=[],
            improvements=[],
            overall_assessment="",
        )
