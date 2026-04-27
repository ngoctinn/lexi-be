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
from domain.services.prompt_validator import validate_conversation_analyzer_response, log_validation_errors

logger = logging.getLogger(__name__)


@dataclass
class TurnAnalysis:
    """Analysis result for a single turn."""

    markdown_vi: str  # Vietnamese markdown
    markdown_en: str  # English markdown
    strengths: list[str]
    mistakes: list[str]
    improvements: list[str]
    suggestions: list[str]  # Better/longer alternative sentences
    overall_assessment: str


class ConversationAnalyzer:
    """Analyzes learner conversation turns using LLM."""

    def __init__(self, bedrock_client=None):
        self.bedrock_client = bedrock_client
        self._model_id = "apac.amazon.nova-lite-v1:0"

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

        # Define JSON schema for structured output (Nova best practice)
        tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": "TurnAnalysis",
                        "description": "Analyze learner's English turn with bilingual feedback and suggestions",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "mistakes_vi": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Mistakes in Vietnamese (explanation) with English examples"
                                    },
                                    "mistakes_en": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Mistakes in English (explanation) with English examples"
                                    },
                                    "improvements_vi": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Improvements in Vietnamese (explanation) with English examples"
                                    },
                                    "improvements_en": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Improvements in English (explanation) with English examples"
                                    },
                                    "suggestions_vi": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Better/longer alternative sentences in Vietnamese with English examples (shown when no mistakes)"
                                    },
                                    "suggestions_en": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Better/longer alternative sentences in English (shown when no mistakes)"
                                    }
                                },
                                "required": []  # All fields optional
                            }
                        }
                    }
                }
            ],
            "toolChoice": {
                "tool": {
                    "name": "TurnAnalysis"
                }
            }
        }

        # Track metrics
        start_time = time.time()
        
        try:
            # Use Converse API with structured output (NON-streaming)
            # AWS SDK automatically retries with exponential backoff + jitter (max 3 attempts)
            # Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/structured-output.html
            response = self.bedrock_client.converse(
                modelId=self._model_id,
                system=[{"text": system_prompt}],
                messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                toolConfig=tool_config,
                inferenceConfig={
                    "maxTokens": 500,
                    "temperature": 0,
                },
            )

            # Extract tool use from response
            input_tokens = response.get("usage", {}).get("inputTokens", 0)
            output_tokens = response.get("usage", {}).get("outputTokens", 0)
            latency_ms = (time.time() - start_time) * 1000
            
            # Find tool use in output
            tool_use_data = None
            for content_block in response.get("output", {}).get("message", {}).get("content", []):
                if "toolUse" in content_block:
                    tool_use_data = content_block["toolUse"]
                    break
            
            # Parse tool use input as JSON
            if tool_use_data and "input" in tool_use_data:
                data = tool_use_data["input"]
            else:
                raise ValueError("No tool use data received from Bedrock")

            # Validate response structure and content
            is_valid, validation_errors = validate_conversation_analyzer_response(data)
            if not is_valid:
                log_validation_errors(validation_errors, "conversation_analyzer response")
                logger.warning(
                    "Response validation failed but continuing with response",
                    extra={
                        "error_count": len(validation_errors),
                        "learner_message": learner_message[:100],
                    }
                )

            # Extract bilingual content from LLM
            mistakes_vi = data.get("mistakes_vi", [])
            mistakes_en = data.get("mistakes_en", [])
            improvements_vi = data.get("improvements_vi", [])
            improvements_en = data.get("improvements_en", [])
            suggestions_vi = data.get("suggestions_vi", [])
            suggestions_en = data.get("suggestions_en", [])

            # Format markdown with proper styling
            markdown_vi = self._format_markdown_vi(mistakes_vi, improvements_vi, suggestions_vi)
            markdown_en = self._format_markdown_en(mistakes_en, improvements_en, suggestions_en)
            
            # Log metrics
            cost_usd = (input_tokens / 1000 * 0.00006) + (output_tokens / 1000 * 0.00024)
            logger.info(
                "Conversation analysis completed",
                extra={
                    "latency_ms": round(latency_ms, 2),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": round(cost_usd, 6),
                    "validation_passed": is_valid,
                    "mistakes_count": len(mistakes_vi),
                    "improvements_count": len(improvements_vi),
                    "suggestions_count": len(suggestions_vi),
                }
            )

            return TurnAnalysis(
                markdown_vi=markdown_vi,
                markdown_en=markdown_en,
                strengths=[],
                mistakes=mistakes_vi,
                improvements=improvements_vi,
                suggestions=suggestions_vi,
                overall_assessment="",
            )

        except json.JSONDecodeError as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(
                "Failed to parse analysis JSON",
                extra={
                    "latency_ms": round(latency_ms, 2),
                    "error_type": "json_decode_error",
                    "error": str(e),
                }
            )
            return self._fallback_analysis()

        except ClientError as e:
            latency_ms = (time.time() - start_time) * 1000
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            logger.error(
                "Bedrock API error after retries",
                extra={
                    "latency_ms": round(latency_ms, 2),
                    "error_code": error_code,
                    "error_message": error_message,
                }
            )
            return self._fallback_analysis()

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.exception(
                "Unexpected error during analysis",
                extra={
                    "latency_ms": round(latency_ms, 2),
                    "error_type": type(e).__name__,
                    "error": str(e),
                }
            )
            return self._fallback_analysis()

    def _build_system_prompt(self, level: str, scenario_context: str) -> str:
        """Build system prompt with explicit formatting instructions.
        
        AWS best practice: Clear instructions reduce ambiguity and improve consistency.
        Reference: https://docs.aws.amazon.com/nova/latest/userguide/prompting-text-understanding.html
        """
        level_guidance = {
            "A1": "Focus on basic errors: vocabulary, verb tense, simple sentence structure.",
            "A2": "Focus on common errors: tense, prepositions, sentence structure.",
            "B1": "Focus on errors affecting clarity: tense, prepositions, connectors.",
            "B2": "Focus on fluency errors: precise vocabulary, complex structures.",
            "C1": "Focus on subtle errors: style, nuance, expression.",
            "C2": "Focus on mastery errors: nuance, register, idiom.",
        }

        return f"""You are an English teacher analyzing errors from Vietnamese learners.

Context: {scenario_context}
Level: {level}
Guidance: {level_guidance.get(level, level_guidance["B1"])}

TASK: Analyze errors, suggest improvements, and provide advanced suggestions
- EXPLAIN in Vietnamese (so learner understands)
- EXAMPLES/CORRECTIONS ALWAYS in English (so learner learns correctly)
- NEVER translate English sentences to Vietnamese

FORMATTING RULES (CRITICAL):
- Mistakes: Use ~~wrong phrase~~ for errors, **correct phrase** for corrections
  Example: "Bạn nhầm lẫn ở ~~go~~ (hiện tại), nên sửa thành **went** (quá khứ)"
- Improvements: Use **better phrase** for suggestions
  Example: "Thay vì 'good', dùng **excellent** sẽ hay hơn"
- Suggestions (when NO mistakes): Provide 2-3 longer/more complex alternative sentences
  Example: "Bạn có thể nói: **I went to the beach with my friends and we had a wonderful time together.**"
- Maximum 2-3 mistakes, 2-3 improvements, 2-3 suggestions
- Return ONLY valid JSON, no markdown wrapper"""

    def _build_user_prompt(self, learner_message: str, ai_response: str, level: str) -> str:
        """Build user prompt with diverse few-shot examples.
        
        AWS best practice: Few-shot prompting with diverse examples improves accuracy.
        - Select diverse examples: Cover A1-C2 levels (common + edge cases)
        - Match complexity levels: Examples match target level complexity
        - Ensure relevance: Examples directly relevant to error types
        
        Reference: https://docs.aws.amazon.com/nova/latest/userguide/prompting-examples.html
        """
        # Few-shot examples (diverse: cover 6 CEFR levels + different error types + suggestions)
        examples = [
            {
                "input": 'Learner: "I go to school yesterday" | Level: A1',
                "output": """{
  "mistakes_vi": ["Bạn nhầm lẫn ở ~~go~~ (hiện tại), nên sửa thành **went** (quá khứ)\\n\\nVì khi có 'yesterday' thì động từ phải ở dạng quá khứ. Dùng **past simple** cho sự kiện đã xảy ra."],
  "mistakes_en": ["You mixed up ~~go~~ (present), should be **went** (past)\\n\\nBecause when you have 'yesterday', the verb needs past tense. Use **past simple** for completed actions."],
  "improvements_vi": [],
  "improvements_en": [],
  "suggestions_vi": [],
  "suggestions_en": []
}"""
            },
            {
                "input": 'Learner: "I like drink coffee" | Level: A2',
                "output": """{
  "mistakes_vi": ["Bạn nhầm lẫn ở ~~drink~~, nên sửa thành **drinking**\\n\\nVì sau 'like' cần dùng gerund (V-ing): **like + V-ing**. Ví dụ: like drinking, like playing."],
  "mistakes_en": ["You mixed up ~~drink~~, should be **drinking**\\n\\nBecause after 'like' you need gerund (V-ing): **like + V-ing**. Examples: like drinking, like playing."],
  "improvements_vi": [],
  "improvements_en": [],
  "suggestions_vi": [],
  "suggestions_en": []
}"""
            },
            {
                "input": 'Learner: "I have went to Paris last year" | Level: B1',
                "output": """{
  "mistakes_vi": ["Bạn nhầm lẫn ở ~~have went~~, nên sửa thành **went**\\n\\nVì có 'last year' (thời điểm cụ thể trong quá khứ) thì dùng **past simple**, không dùng present perfect."],
  "mistakes_en": ["You mixed up ~~have went~~, should be **went**\\n\\nBecause 'last year' (specific past time) requires **past simple**, not present perfect."],
  "improvements_vi": ["Thay vì chỉ nói 'went to Paris', bạn có thể thêm chi tiết: **I visited Paris last year and explored the Eiffel Tower**"],
  "improvements_en": ["Instead of just 'went to Paris', you can add details: **I visited Paris last year and explored the Eiffel Tower**"],
  "suggestions_vi": [],
  "suggestions_en": []
}"""
            },
            {
                "input": 'Learner: "If I would have more time, I will travel more" | Level: B2',
                "output": """{
  "mistakes_vi": ["Bạn nhầm lẫn ở ~~If I would have~~, nên sửa thành **If I had**\\n\\nVì đây là câu điều kiện loại 2 (unreal present): **If + past simple, would + V**. Không dùng 'would' trong mệnh đề if."],
  "mistakes_en": ["You mixed up ~~If I would have~~, should be **If I had**\\n\\nBecause this is second conditional (unreal present): **If + past simple, would + V**. Don't use 'would' in the if-clause."],
  "improvements_vi": [],
  "improvements_en": [],
  "suggestions_vi": [],
  "suggestions_en": []
}"""
            },
            {
                "input": 'Learner: "The company should make laws more strict" | Level: C1',
                "output": """{
  "mistakes_vi": [],
  "mistakes_en": [],
  "improvements_vi": ["Thay vì ~~more strict~~, dùng **stricter** (comparative form)\\n\\nVì 'strict' là tính từ ngắn, dùng **-er** thay vì 'more'. Hoặc dùng **more stringent** (sophisticated vocabulary) cho C1."],
  "improvements_en": ["Instead of ~~more strict~~, use **stricter** (comparative form)\\n\\nBecause 'strict' is a short adjective, use **-er** instead of 'more'. Or use **more stringent** (sophisticated vocabulary) for C1."],
  "suggestions_vi": [],
  "suggestions_en": []
}"""
            },
            {
                "input": 'Learner: "I like coffee" | Level: A1 (NO MISTAKES)',
                "output": """{
  "mistakes_vi": [],
  "mistakes_en": [],
  "improvements_vi": [],
  "improvements_en": [],
  "suggestions_vi": ["Bạn có thể nói dài hơn: **I like drinking coffee in the morning because it helps me wake up**", "Hoặc: **I really enjoy a hot cup of coffee, especially when I'm studying**"],
  "suggestions_en": ["You could say more: **I like drinking coffee in the morning because it helps me wake up**", "Or: **I really enjoy a hot cup of coffee, especially when I'm studying**"]
}"""
            }
        ]

        prompt = f"""Learner message: "{learner_message}"
AI response: "{ai_response}"
Level: {level}

EXAMPLES (few-shot - diverse levels and error types):
Example 1 (A1 - Tense error): {examples[0]['input']}
Output: {examples[0]['output']}

Example 2 (A2 - Gerund error): {examples[1]['input']}
Output: {examples[1]['output']}

Example 3 (B1 - Tense + Improvement): {examples[2]['input']}
Output: {examples[2]['output']}

Example 4 (B2 - Conditional error): {examples[3]['input']}
Output: {examples[3]['output']}

Example 5 (C1 - Style improvement): {examples[4]['input']}
Output: {examples[4]['output']}

Example 6 (A1 - NO MISTAKES - Show suggestions): {examples[5]['input']}
Output: {examples[5]['output']}

NOW, analyze this learner message:
Learner: "{learner_message}" | Level: {level}

IMPORTANT: If there are NO mistakes, provide 2-3 suggestions for longer/more complex sentences instead.

Return ONLY the JSON object (no preamble, no markdown wrapper)."""

        return prompt

    def _format_markdown_vi(self, mistakes: list[str], improvements: list[str], suggestions: list[str] = None) -> str:
        if suggestions is None:
            suggestions = []
            
        sections = []

        if mistakes:
            for mistake in mistakes:
                sections.append(f"⚠️ {mistake}\n")
        
        if improvements:
            for improvement in improvements:
                sections.append(f"💡 {improvement}\n")
        
        # Khi không có lỗi: khích lệ trước, sau đó gợi ý
        if not mistakes and not improvements:
            sections.append("### ✅ Tuyệt vời!\n")
            sections.append("Câu của bạn hoàn toàn chính xác! Bạn đang tiến bộ rất tốt.\n\n")
            
            if suggestions:
                sections.append("### 🌟 Gợi ý nâng cao:\n")
                sections.append("Để nâng cao kỹ năng, bạn có thể thử những cách nói dài hơn hoặc phức tạp hơn:\n\n")
                for suggestion in suggestions:
                    sections.append(f"✨ {suggestion}\n")
            else:
                sections.append("Hãy thử nói những câu dài hơn hoặc phức tạp hơn để tiếp tục cải thiện!\n")
        elif suggestions:
            sections.append("### 🌟 Gợi ý nâng cao:\n")
            for suggestion in suggestions:
                sections.append(f"✨ {suggestion}\n")

        return "".join(sections) if sections else "✅ Tuyệt vời! Câu của bạn hoàn toàn chính xác."

    def _format_markdown_en(self, mistakes: list[str], improvements: list[str], suggestions: list[str] = None) -> str:
        if suggestions is None:
            suggestions = []
            
        sections = []

        if mistakes:
            for mistake in mistakes:
                sections.append(f"⚠️ {mistake}\n")
        
        if improvements:
            for improvement in improvements:
                sections.append(f"💡 {improvement}\n")
        
        # Khi không có lỗi: khích lệ trước, sau đó gợi ý
        if not mistakes and not improvements:
            sections.append("### ✅ Excellent!\n")
            sections.append("Your sentence is completely correct! You're making great progress.\n\n")
            
            if suggestions:
                sections.append("### 🌟 Advanced Suggestions:\n")
                sections.append("To improve further, try speaking with longer or more complex sentences:\n\n")
                for suggestion in suggestions:
                    sections.append(f"✨ {suggestion}\n")
            else:
                sections.append("Try speaking with longer or more complex sentences to continue improving!\n")
        elif suggestions:
            sections.append("### 🌟 Advanced Suggestions:\n")
            for suggestion in suggestions:
                sections.append(f"✨ {suggestion}\n")

        return "".join(sections) if sections else "✅ Excellent! Your sentence is completely correct."

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
