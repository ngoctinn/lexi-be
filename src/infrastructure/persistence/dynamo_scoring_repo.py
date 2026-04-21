from datetime import datetime, timezone
from typing import List
import os

import boto3
from boto3.dynamodb.conditions import Key

from application.repositories.scoring_repository import ScoringRepository
from domain.entities.scoring import Scoring


class DynamoScoringRepo(ScoringRepository):
    def __init__(self, table=None):
        self._table = table or boto3.resource("dynamodb").Table(os.environ["LEXI_TABLE_NAME"])

    def save(self, score: Scoring) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._table.put_item(
            Item={
                "PK": f"SESSION#{score.session_id}",
                "SK": "SCORING",
                "GSI1PK": f"USER#{score.user_id}#SCORING",
                "GSI1SK": now,
                "GSI3PK": "SCORING",
                "GSI3SK": now,
                "EntityType": "SCORING",
                "scoring_id": str(score.scoring_id),
                "session_id": str(score.session_id),
                "user_id": score.user_id,
                "fluency_score": score.fluency_score,
                "pronunciation_score": score.pronunciation_score,
                "grammar_score": score.grammar_score,
                "vocabulary_score": score.vocabulary_score,
                "overall_score": score.overall_score,
                "feedback": score.feedback,
                "created_at": now,
                "updated_at": now,
            }
        )

    def get_by_session(self, session_id: str) -> List[Scoring]:
        response = self._table.query(
            KeyConditionExpression=Key("PK").eq(f"SESSION#{session_id}") & Key("SK").begins_with("SCORING"),
        )
        return [self._to_entity(item) for item in response.get("Items", [])]

    def get_user_progress(self, user_id: str, limit: int = 50) -> List[Scoring]:
        response = self._table.query(
            IndexName="GSI1-UserEntity-Time",
            KeyConditionExpression=Key("GSI1PK").eq(f"USER#{user_id}#SCORING"),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [self._to_entity(item) for item in response.get("Items", [])]

    def _to_entity(self, item: dict) -> Scoring:
        return Scoring(
            scoring_id=item.get("scoring_id", ""),
            session_id=item.get("session_id", ""),
            user_id=item.get("user_id", ""),
            fluency_score=item.get("fluency_score", 0),
            pronunciation_score=item.get("pronunciation_score", 0),
            grammar_score=item.get("grammar_score", 0),
            vocabulary_score=item.get("vocabulary_score", 0),
            overall_score=item.get("overall_score", 0),
            feedback=item.get("feedback", ""),
        )
