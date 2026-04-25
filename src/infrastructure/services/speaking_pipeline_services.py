from __future__ import annotations

import hashlib
import json
import logging
import re
import os
import time
import urllib.request
from typing import List

from shared.http_utils import dumps

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

# ============================================================================
# AWS Best Practice: Initialize SDK clients outside handler (module-level)
# Reference: https://docs.aws.amazon.com/amazonq/detector-library/python/lambda-client-reuse/
# ============================================================================

# Configure retry with exponential backoff + jitter (AWS recommended)
# Per: https://aws.amazon.com/blogs/machine-learning/optimize-your-applications-for-scale-and-reliability-on-amazon-bedrock/
_RETRY_CONFIG = Config(
    retries={
        "max_attempts": 3,  # Total attempts (1 initial + 2 retries)
        "mode": "adaptive",  # Exponential backoff with jitter
    }
)

# Module-level clients (reused across Lambda invocations)
_bedrock_client = boto3.client("bedrock-runtime", config=_RETRY_CONFIG)
_comprehend_client = boto3.client("comprehend")
_transcribe_client = boto3.client("transcribe")
_polly_client = boto3.client("polly")
_s3_client = boto3.client("s3", config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'}))

from application.service_ports.speaking_services import (
    ConversationGenerationService,
    SpeakingAnalysis,
    SpeechSynthesisService,
    TranscriptAnalysisService,
)
from domain.entities.session import Session
from domain.entities.turn import Turn
from domain.value_objects.enums import ProficiencyLevel, Speaker
from domain.services.prompt_builder import OptimizedPromptBuilder
from shared.utils.ulid_util import new_ulid


logger = logging.getLogger(__name__)

# Model ID - Use inference profile for cross-region support
# Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-use.html
# Direct model ID: "amazon.nova-micro-v1:0" (only works in us-east-1, us-west-2)
# Inference profile: "apac.amazon.nova-micro-v1:0" (works in APAC regions)
_BEDROCK_MODEL_ID = "apac.amazon.nova-micro-v1:0"

# Sliding window: chỉ gửi N turns gần nhất vào LLM context
_MAX_HISTORY_TURNS = 10


def _enum_value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _build_llm_system_prompt(session: Session) -> list[dict]:
    """
    Build optimized system prompt for Nova model.
    
    Reference: https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html
    
    Returns list of system content blocks.
    """
    level = _enum_value(session.level)
    
    # Get cache-optimized prompt split
    static_prefix, dynamic_suffix = OptimizedPromptBuilder.build_with_cache_split(
        scenario_title=session.scenario_title,
        learner_role=session.learner_role_id,
        ai_role=session.ai_role_id,
        level=level,
        selected_goals=session.selected_goals,
        ai_gender=_enum_value(session.ai_gender),
    )
    
    # Return as list of system content blocks
    # Per AWS docs: system is list of {"text": "string"} objects
    return [
        {"text": static_prefix},
        {"text": dynamic_suffix}
    ]


def _build_messages_for_llm(turns: List[Turn]) -> List[dict]:
    """Sliding window: lấy N turns gần nhất, format cho Bedrock Messages API (Nova format)."""
    recent = sorted(turns, key=lambda t: t.turn_index)[-_MAX_HISTORY_TURNS:]
    messages = []
    for turn in recent:
        role = "user" if _enum_value(turn.speaker) == Speaker.USER.value else "assistant"
        # Nova format: content must be list of objects
        messages.append({
            "role": role,
            "content": [{"text": turn.content}]
        })

    # Bedrock yêu cầu messages phải bắt đầu bằng role "user"
    if not messages:
        messages = [{"role": "user", "content": [{"text": "Hello"}]}]
    elif messages[0]["role"] != "user":
        messages = [{"role": "user", "content": [{"text": "Hello"}]}] + messages

    return messages


class ComprehendTranscriptAnalysisService(TranscriptAnalysisService):
    def __init__(self, client=None):
        # Use module-level client if not provided (for testing)
        self._client = client if client is not None else _comprehend_client

    def analyze(self, text: str) -> SpeakingAnalysis:
        cleaned_text = text.strip()
        if not cleaned_text:
            return SpeakingAnalysis()

        if len(cleaned_text) < 20:
            return self._fallback_analysis(cleaned_text)

        try:
            # Use cached client (no recreation)
            client = self._client
            key_phrases_response = client.detect_key_phrases(
                Text=cleaned_text,
                LanguageCode="en",
            )
            syntax_response = client.detect_syntax(
                Text=cleaned_text,
                LanguageCode="en",
            )
            # Detect dominant language để nhận biết user nói tiếng Việt
            lang_response = client.detect_dominant_language(Text=cleaned_text)
            dominant_lang = (
                lang_response["Languages"][0]["LanguageCode"]
                if lang_response.get("Languages")
                else "en"
            )

            key_phrases = [
                phrase.get("Text", "").strip()
                for phrase in key_phrases_response.get("KeyPhrases", [])
                if phrase.get("Text")
            ]
            syntax_notes = [
                f"{token.get('Text', '')}:{token.get('PartOfSpeech', {}).get('Tag', '')}"
                for token in syntax_response.get("SyntaxTokens", [])
                if token.get("Text") and token.get("PartOfSpeech", {}).get("Tag") not in {"PUNCT", "ROOT"}
            ][:8]
            return SpeakingAnalysis(
                key_phrases=key_phrases[:5],
                word_count=len(re.findall(r"[A-Za-z']+", cleaned_text)),
                unique_word_count=len({word.lower() for word in re.findall(r"[A-Za-z']+", cleaned_text)}),
                sentence_count=max(1, len(re.findall(r"[.!?]", cleaned_text)) or 1),
                syntax_notes=syntax_notes,
                dominant_language=dominant_lang,
            )
        except Exception:
            logger.exception("Comprehend analysis failed, falling back to local heuristics")
            return self._fallback_analysis(cleaned_text)

    def _fallback_analysis(self, text: str) -> SpeakingAnalysis:
        words = re.findall(r"[A-Za-z']+", text)
        key_phrases = self._extract_key_phrases(words)
        return SpeakingAnalysis(
            key_phrases=key_phrases,
            word_count=len(words),
            unique_word_count=len({word.lower() for word in words}),
            sentence_count=max(1, len(re.findall(r"[.!?]", text)) or 1),
            syntax_notes=[],
        )

    def _extract_key_phrases(self, words: List[str]) -> List[str]:
        phrases: List[str] = []
        current: List[str] = []
        for word in words:
            cleaned = word.strip()
            if not cleaned:
                continue
            current.append(cleaned)
            if len(current) == 2:
                phrases.append(" ".join(current))
                current = []
            if len(phrases) == 5:
                break
        if not phrases and words:
            phrases.append(words[0])
        return phrases


class RuleBasedConversationGenerationService(ConversationGenerationService):
    """Fallback khi Bedrock không khả dụng."""
    def generate_reply(
        self,
        session: Session,
        user_turn: Turn,
        analysis: SpeakingAnalysis,
        turn_history: List[Turn],
    ) -> str:
        topic = analysis.key_phrases[0] if analysis.key_phrases else "that idea"
        goal = session.selected_goals[0] if session.selected_goals else "the task"
        level = _enum_value(session.level)

        if level in {ProficiencyLevel.A1.value, ProficiencyLevel.A2.value}:
            return f"Good answer. Can you say one more simple sentence about {topic}?"

        if level in {ProficiencyLevel.B1.value, ProficiencyLevel.B2.value}:
            return f"That sounds clear. Could you expand a little more on {topic} and connect it to {goal.lower()}?"

        return f"Interesting point. Please explain how {topic} supports {goal.lower()} and give one concrete example."


class BedrockConversationGenerationService(ConversationGenerationService):
    """
    AI conversation generation dùng Amazon Bedrock Nova Micro.
    Model ID: amazon.nova-micro-v1:0
    Docs: https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
    
    Error Handling:
    - 429 ThrottlingException: Handled by boto3 exponential backoff (configured at module init)
    - 503 ServiceUnavailableException: Handled by boto3 exponential backoff
    - Other errors: Logged and fallback response returned
    """

    def __init__(self, bedrock_client=None):
        """
        Initialize with module-level client (AWS best practice).
        
        Args:
            bedrock_client: Optional boto3 Bedrock client. If not provided, uses module-level
                          client with exponential backoff retry configuration.
        """
        # Use module-level client if not provided (for testing)
        self._bedrock = bedrock_client if bedrock_client is not None else _bedrock_client

    def generate_reply(
        self,
        session: Session,
        user_turn: Turn,
        analysis: SpeakingAnalysis,
        turn_history: List[Turn],
    ) -> str:
        """
        Generate reply using Bedrock with optimized prompt caching.
        
        AWS Best Practices Applied:
        1. Streaming API for better TTFT
        2. Cache-optimized prompt (static prefix + dynamic suffix)
        3. Exponential backoff retry (configured at module init)
        
        References:
        - Streaming: https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/invoke_model_with_response_stream.html
        - Caching: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
        """
        system_content = _build_llm_system_prompt(session)  # Returns list with cache checkpoint
        messages = _build_messages_for_llm(turn_history + [user_turn])

        # Thêm language hint nếu user không nói tiếng Anh
        if analysis.dominant_language != "en":
            messages[-1]["content"] += (
                f"\n[Note: The learner wrote in {analysis.dominant_language}. "
                "Gently remind them to use English and provide a simple English prompt.]"
            )

        # AWS Nova format (not Anthropic)
        # Reference: https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html
        body = dumps({
            "system": system_content,  # List with cache checkpoint
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": 150,
                "temperature": 0.7,
            }
        })

        try:
            # AWS Best Practice: Use streaming API for better TTFT
            # Reference: https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/invoke_model_with_response_stream.html
            response = self._bedrock.invoke_model_with_response_stream(
                modelId=_BEDROCK_MODEL_ID,
                body=body,
            )
            
            # Process event stream
            event_stream = response["body"]
            text = ""
            
            for event in event_stream:
                # Handle chunk event (contains response text)
                if "chunk" in event:
                    chunk_bytes = event["chunk"]["bytes"]
                    chunk_json = json.loads(chunk_bytes.decode("utf-8"))
                    
                    # Extract text from chunk (Nova format)
                    # Reference: https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html
                    if "contentBlockDelta" in chunk_json:
                        delta = chunk_json["contentBlockDelta"].get("delta", {})
                        if "text" in delta:
                            text += delta["text"]
                    # Fallback for other formats
                    elif "delta" in chunk_json and "text" in chunk_json["delta"]:
                        text += chunk_json["delta"]["text"]
                    elif "content" in chunk_json and len(chunk_json["content"]) > 0:
                        text += chunk_json["content"][0].get("text", "")
                
                # Handle error events (per AWS docs)
                elif "internalServerException" in event:
                    error = event["internalServerException"]
                    logger.error(f"Bedrock internal error: {error.get('message', 'Unknown')}")
                    break
                
                elif "modelStreamErrorException" in event:
                    error = event["modelStreamErrorException"]
                    logger.error(f"Bedrock stream error: {error.get('message', 'Unknown')}")
                    break
                
                elif "throttlingException" in event:
                    error = event["throttlingException"]
                    logger.warning(f"Bedrock throttled: {error.get('message', 'Unknown')}")
                    break
                
                elif "modelTimeoutException" in event:
                    error = event["modelTimeoutException"]
                    logger.warning(f"Bedrock timeout: {error.get('message', 'Unknown')}")
                    break
                
                elif "validationException" in event:
                    error = event["validationException"]
                    logger.error(f"Bedrock validation error: {error.get('message', 'Unknown')}")
                    break
                
                elif "serviceUnavailableException" in event:
                    error = event["serviceUnavailableException"]
                    logger.warning(f"Bedrock unavailable: {error.get('message', 'Unknown')}")
                    break
            
            if text:
                return text.strip()
            else:
                # Fallback if no text received
                logger.warning("No text received from Bedrock stream")
                return "I see. Could you tell me more about that?"
            
        except ClientError as e:
            # AWS API error - distinguish between error types
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            
            if error_code == "ThrottlingException":
                # 429: Quota exceeded - boto3 already retried with exponential backoff
                logger.warning(
                    f"Bedrock throttled (429): session={session.session_id}, "
                    f"turn={user_turn.turn_index}, level={_enum_value(session.level)}"
                )
            elif error_code == "ServiceUnavailableException":
                # 503: Service temporarily unavailable - boto3 already retried
                logger.warning(
                    f"Bedrock unavailable (503): session={session.session_id}, "
                    f"turn={user_turn.turn_index}"
                )
            else:
                # Other AWS errors (ValidationException, etc.)
                logger.error(
                    f"Bedrock API error ({error_code}): session={session.session_id}, "
                    f"turn={user_turn.turn_index}, message={str(e)}"
                )
            
            # Fallback response (graceful degradation)
            return "I see. Could you tell me more about that?"
            
        except Exception as e:
            # Non-AWS errors (JSON parsing, network, etc.)
            error_type = type(e).__name__
            logger.error(
                f"Bedrock generation error ({error_type}): session={session.session_id}, "
                f"turn={user_turn.turn_index}, message={str(e)}",
                exc_info=True
            )
            
            # Fallback response
            return "I see. Could you tell me more about that?"


class TranscribeSTTService:
    """
    Speech-to-text dùng Amazon Transcribe batch job.
    Pattern: StartTranscriptionJob → poll GetTranscriptionJob → lấy transcript.
    Docs: https://docs.aws.amazon.com/code-library/latest/ug/python_3_transcribe_code_examples.html
    """

    _MAX_POLL = 15       # max 15 lần poll
    _POLL_INTERVAL = 2   # 2 giây mỗi lần → max 30s timeout

    def __init__(self, transcribe_client=None):
        # Use module-level client if not provided (for testing)
        self._client = transcribe_client if transcribe_client is not None else _transcribe_client

    def transcribe(self, s3_bucket: str, s3_key: str) -> tuple[str, float]:
        """
        Returns (transcript_text, confidence).
        confidence = 1.0 nếu COMPLETED, 0.0 nếu FAILED/timeout.
        """
        job_name = f"lexi-{new_ulid()}"
        media_uri = f"s3://{s3_bucket}/{s3_key}"

        # Detect format từ extension
        if s3_key.endswith(".mp3"):
            media_format = "mp3"
        elif s3_key.endswith(".wav"):
            media_format = "wav"
        else:
            media_format = "webm"

        # Use cached client (no recreation)
        client = self._client

        try:
            client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={"MediaFileUri": media_uri},
                MediaFormat=media_format,
                LanguageCode="en-US",
            )
        except Exception:
            logger.exception("Failed to start transcription job")
            return "", 0.0

        # Poll kết quả — pattern từ AWS docs
        for _ in range(self._MAX_POLL):
            time.sleep(self._POLL_INTERVAL)
            try:
                job = client.get_transcription_job(TranscriptionJobName=job_name)
                status = job["TranscriptionJob"]["TranscriptionJobStatus"]

                if status == "COMPLETED":
                    transcript_uri = job["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                    with urllib.request.urlopen(transcript_uri) as resp:
                        data = json.loads(resp.read())
                    text = data["results"]["transcripts"][0]["transcript"]
                    # Cleanup job để tránh tích lũy
                    try:
                        client.delete_transcription_job(TranscriptionJobName=job_name)
                    except Exception:
                        pass
                    return text, 1.0

                if status == "FAILED":
                    logger.warning("Transcription job %s failed", job_name)
                    return "", 0.0

            except Exception:
                logger.exception("Error polling transcription job %s", job_name)
                return "", 0.0

        logger.warning("Transcription job %s timed out", job_name)
        return "", 0.0


class PollySpeechSynthesisService(SpeechSynthesisService):
    def __init__(self, client=None, s3_client=None):
        # Use module-level clients if not provided (for testing)
        self._client = client if client is not None else _polly_client
        self._s3_client = s3_client if s3_client is not None else _s3_client

    def synthesize(self, text: str, ai_gender: str, object_key: str | None = None) -> str:
        cleaned_text = text.strip()
        if not cleaned_text:
            return ""

        try:
            # Use cached clients (no recreation)
            client = self._client
            s3_client = self._s3_client
            bucket_name = os.environ.get("SPEAKING_AUDIO_BUCKET_NAME")
            if not bucket_name:
                logger.warning("SPEAKING_AUDIO_BUCKET_NAME is not configured")
                return ""
            voice_id = self._resolve_voice(ai_gender)
            response = client.synthesize_speech(
                Text=cleaned_text,
                OutputFormat="mp3",
                VoiceId=voice_id,
            )
            audio_stream = response.get("AudioStream")
            if not audio_stream:
                return ""
            audio_bytes = audio_stream.read()
            if not audio_bytes:
                return ""
            key = object_key or self._default_object_key(cleaned_text, voice_id)
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=audio_bytes,
                ContentType="audio/mpeg",
            )
            return s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": bucket_name, "Key": key},
                ExpiresIn=3600,
            )
        except Exception:
            logger.exception("Polly synthesis failed")
            return ""

    def _resolve_voice(self, ai_gender: str) -> str:
        normalized = str(ai_gender).strip().lower()
        if normalized == "male":
            return "Matthew"
        return "Joanna"

    def _default_object_key(self, text: str, voice_id: str) -> str:
        digest = hashlib.sha1(f"{voice_id}:{text}".encode("utf-8")).hexdigest()
        return f"speaking/audio/{digest}.mp3"
