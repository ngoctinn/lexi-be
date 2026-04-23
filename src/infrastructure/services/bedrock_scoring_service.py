import json
import logging
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from application.services.llm_scoring_service import LlmScoringService, ScoringResult

logger = logging.getLogger(__name__)

_BEDROCK_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime")
    return _client


class BedrockScoringService(LlmScoringService):
    """Adapter: Amazon Bedrock Claude → LlmScoringService port."""

    def score_session(
        self,
        scenario_title: str,
        level: str,
        goals: str,
        learner_transcript: str,
    ) -> ScoringResult:
        prompt = (
            f"You are an English language examiner. Evaluate this learner's performance.\n\n"
            f"SCENARIO: {scenario_title}\nLEVEL: {level}\nGOALS: {goals}\n\n"
            f"LEARNER'S TURNS:\n{learner_transcript or '(No turns recorded)'}\n\n"
            f"Score each from 0-100. Respond ONLY with valid JSON:\n"
            f'{{\"fluency\": <int>, \"grammar\": <int>, \"vocabulary\": <int>, '
            f'\"overall\": <int>, \"feedback\": \"<2 sentences in Vietnamese>\"}}'
        )

        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            })
            response = _get_client().invoke_model(modelId=_BEDROCK_MODEL_ID, body=body)
            result = json.loads(response["body"].read())
            scores = json.loads(result["content"][0]["text"].strip())

            return ScoringResult(
                fluency=max(0, min(100, int(scores.get("fluency", 70)))),
                grammar=max(0, min(100, int(scores.get("grammar", 70)))),
                vocabulary=max(0, min(100, int(scores.get("vocabulary", 70)))),
                overall=max(0, min(100, int(scores.get("overall", 70)))),
                feedback=scores.get("feedback", "Bạn đã hoàn thành phiên học."),
            )
        except Exception:
            logger.exception("Bedrock scoring failed")
            raise
