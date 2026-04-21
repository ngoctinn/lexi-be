from __future__ import annotations

import hashlib
import logging
import re
import os
from typing import List

import boto3

from application.services.speaking_services import (
    ConversationGenerationService,
    SpeakingAnalysis,
    SpeechSynthesisService,
    TranscriptAnalysisService,
)
from domain.entities.session import Session
from domain.entities.turn import Turn
from domain.value_objects.enums import ProficiencyLevel


logger = logging.getLogger(__name__)


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
    def generate_reply(
        self,
        session: Session,
        user_turn: Turn,
        analysis: SpeakingAnalysis,
        turn_history: List[Turn],
    ) -> str:
        topic = analysis.key_phrases[0] if analysis.key_phrases else "that idea"
        goal = session.selected_goals[0] if session.selected_goals else "the task"
        level = session.level.value if hasattr(session.level, "value") else str(session.level)

        if level in {ProficiencyLevel.A1.value, ProficiencyLevel.A2.value}:
            return f"Good answer. Can you say one more simple sentence about {topic}?"

        if level in {ProficiencyLevel.B1.value, ProficiencyLevel.B2.value}:
            return f"That sounds clear. Could you expand a little more on {topic} and connect it to {goal.lower()}?"

        return f"Interesting point. Please explain how {topic} supports {goal.lower()} and give one concrete example."


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
