from datetime import datetime, timezone
from typing import List, Optional
import os
import logging

import boto3
from boto3.dynamodb.conditions import Key

from application.repositories.session_repository import SessionRepository
from domain.entities.session import Session
from domain.value_objects.enums import Gender, ProficiencyLevel

logger = logging.getLogger(__name__)


class DynamoSessionRepo(SessionRepository):
    def __init__(self, table=None):
        self._table = table or boto3.resource("dynamodb").Table(os.environ["LEXI_TABLE_NAME"])

    def save(self, session: Session) -> None:
        now = datetime.now(timezone.utc).isoformat()
        created_at = session.created_at or now
        updated_at = session.updated_at or now

        session.created_at = created_at
        session.updated_at = updated_at

        self._table.put_item(
            Item={
                "PK": f"SESSION#{session.session_id}",
                "SK": "METADATA",
                "GSI1PK": f"USER#{session.user_id}#SESSION",
                "GSI1SK": updated_at,
                "GSI3PK": "SESSION",
                "GSI3SK": updated_at,
                "EntityType": "SESSION",
                "session_id": str(session.session_id),
                "user_id": session.user_id,
                "scenario_id": str(session.scenario_id),
                "learner_role_id": session.learner_role_id,
                "ai_role_id": session.ai_role_id,
                "ai_gender": session.ai_gender.value if hasattr(session.ai_gender, "value") else session.ai_gender,
                "level": session.level.value if hasattr(session.level, "value") else session.level,
                "selected_goals": list(session.selected_goals),
                "prompt_snapshot": session.prompt_snapshot,
                "status": session.status,
                "total_turns": session.total_turns,
                "user_turns": session.user_turns,
                "hint_used_count": session.hint_used_count,
                "connection_id": session.connection_id,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    def get_by_id(self, session_id: str) -> Optional[Session]:
        response = self._table.get_item(
            Key={
                "PK": f"SESSION#{session_id}",
                "SK": "METADATA",
            }
        )
        item = response.get("Item")
        if not item:
            return None

        try:
            return self._to_entity(item)
        except Exception as exc:
            # Malformed item in DB, log and return None instead of raising
            logger.warning("get_by_id malformed item for session_id=%s: %s", session_id, exc)
            return None

    def get_active_session(self, user_id: str) -> Optional[Session]:
        response = self._table.query(
            IndexName="GSI1-UserEntity-Time",
            KeyConditionExpression=Key("GSI1PK").eq(f"USER#{user_id}#SESSION"),
            ScanIndexForward=False,
            Limit=20,
        )

        for item in response.get("Items", []):
            try:
                session = self._to_entity(item)
            except Exception as exc:
                logger.warning("get_active_session skipping malformed item: %s", exc)
                continue

            if session.status != "COMPLETED":
                return session

        return None

    def list_by_user(self, user_id: str, limit: int = 10) -> List[Session]:
        response = self._table.query(
            IndexName="GSI1-UserEntity-Time",
            KeyConditionExpression=Key("GSI1PK").eq(f"USER#{user_id}#SESSION"),
            ScanIndexForward=False,
            Limit=limit,
        )
        sessions: list[Session] = []
        for item in response.get("Items", []):
            try:
                sessions.append(self._to_entity(item))
            except Exception as exc:
                # Log and skip malformed DB records instead of failing the whole request
                logger.warning("list_by_user skipping malformed item: %s", exc)
                continue

        return sessions

    def _to_entity(self, item: dict) -> Session:
        return Session(
            session_id=item.get("session_id", ""),
            scenario_id=item.get("scenario_id", ""),
            user_id=item.get("user_id", ""),
            learner_role_id=item.get("learner_role_id", ""),
            ai_role_id=item.get("ai_role_id", ""),
            ai_gender=Gender(item.get("ai_gender", Gender.FEMALE.value)),
            level=ProficiencyLevel(item.get("level", ProficiencyLevel.B1.value)),
            selected_goals=list(item.get("selected_goals") or []),
            prompt_snapshot=item.get("prompt_snapshot", ""),
            status=item.get("status", "ACTIVE"),
            total_turns=item.get("total_turns", 0),
            user_turns=item.get("user_turns", 0),
            hint_used_count=item.get("hint_used_count", 0),
            connection_id=item.get("connection_id", ""),
            created_at=item.get("created_at", ""),
            updated_at=item.get("updated_at", ""),
        )
