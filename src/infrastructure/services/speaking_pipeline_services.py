from __future__ import annotations

import hashlib
import json
import logging
import re
import os
import time
import urllib.request
from typing import List

import boto3
from botocore.exceptions import ClientError

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

# Model ID từ AWS docs: https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
_BEDROCK_MODEL_ID = "amazon.nova-micro-v1:0"

# Sliding window: chỉ gửi N turns gần nhất vào LLM context
_MAX_HISTORY_TURNS = 10


def _enum_value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _build_llm_system_prompt(session: Session) -> str:
    """
    Build optimized 5-section system prompt using OptimizedPromptBuilder.
    
    Replaces old generic prompt with structured format:
    1. IDENTITY: Role, relationship, purpose
    2. PERSONALITY: Traits, emotional tone (level-adaptive)
    3. BEHAVIORS: Conversational patterns
    4. RESPONSE RULES: Format constraints, delivery cues
    5. GUARDRAILS: Off-topic, Vietnamese, inappropriate language
    """
    level = _enum_value(session.level)
    
    return OptimizedPromptBuilder.build(
        scenario_title=session.scenario_title,
        learner_role=session.learner_role_id,
        ai_role=session.ai_role_id,
        level=level,
        selected_goals=session.selected_goals,
        ai_gender=_enum_value(session.ai_gender),
    )


def _build_messages_for_llm(turns: List[Turn]) -> List[dict]:
    """Sliding window: lấy N turns gần nhất, format cho Bedrock Messages API."""
    recent = sorted(turns, key=lambda t: t.turn_index)[-_MAX_HISTORY_TURNS:]
    messages = []
    for turn in recent:
        role = "user" if _enum_value(turn.speaker) == Speaker.USER.value else "assistant"
        messages.append({"role": role, "content": turn.content})

    # Bedrock yêu cầu messages phải bắt đầu bằng role "user"
    if not messages:
        messages = [{"role": "user", "content": "Hello"}]
    elif messages[0]["role"] != "user":
        messages = [{"role": "user", "content": "Hello"}] + messages

    return messages


class ComprehendTranscriptAnalysisService(TranscriptAnalysisService):
    def __init__(self, client=None):
        self._client = client

    def analyze(self, text: str) -> SpeakingAnalysis:
        cleaned_text = text.strip()
        if not cleaned_text:
            return SpeakingAnalysis()

        if len(cleaned_text) < 20:
            return self._fallback_analysis(cleaned_text)

        try:
            client = self._client or boto3.client("comprehend")
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
    """

    def __init__(self, bedrock_client=None):
        self._bedrock = bedrock_client

    def generate_reply(
        self,
        session: Session,
        user_turn: Turn,
        analysis: SpeakingAnalysis,
        turn_history: List[Turn],
    ) -> str:
        system_prompt = _build_llm_system_prompt(session)
        messages = _build_messages_for_llm(turn_history + [user_turn])

        # Thêm language hint nếu user không nói tiếng Anh
        if analysis.dominant_language != "en":
            messages[-1]["content"] += (
                f"\n[Note: The learner wrote in {analysis.dominant_language}. "
                "Gently remind them to use English and provide a simple English prompt.]"
            )

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 150,
            "system": system_prompt,
            "messages": messages,
            "temperature": 0.7,
        })

        try:
            client = self._bedrock or boto3.client("bedrock-runtime")
            response = client.invoke_model(
                modelId=_BEDROCK_MODEL_ID,
                body=body,
            )
            result = json.loads(response["body"].read())
            return result["content"][0]["text"].strip()
        except Exception:
            logger.exception("Bedrock generation failed, using fallback")
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
        self._client = transcribe_client

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

        client = self._client or boto3.client("transcribe")

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
        self._client = client
        self._s3_client = s3_client

    def synthesize(self, text: str, ai_gender: str, object_key: str | None = None) -> str:
        cleaned_text = text.strip()
        if not cleaned_text:
            return ""

        try:
            client = self._client or boto3.client("polly")
            s3_client = self._s3_client or boto3.client("s3")
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
