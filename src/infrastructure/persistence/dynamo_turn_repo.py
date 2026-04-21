from datetime import datetime, timezone
from typing import List
import os

import boto3
from boto3.dynamodb.conditions import Key

from application.repositories.turn_repository import TurnRepository
from domain.entities.turn import Turn
from domain.value_objects.enums import Speaker


class DynamoTurnRepo(TurnRepository):
    def __init__(self, table=None):
        self._table = table or boto3.resource("dynamodb").Table(os.environ["LEXI_TABLE_NAME"])

    def save(self, turn: Turn) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._table.put_item(
            Item={
                "PK": f"SESSION#{turn.session_id}",
                "SK": f"TURN#{turn.turn_index}",
                "GSI3PK": "TURN",
                "GSI3SK": now,
                "EntityType": "TURN",
                "session_id": str(turn.session_id),
                "turn_index": turn.turn_index,
                "speaker": turn.speaker.value if hasattr(turn.speaker, "value") else turn.speaker,
                "content": turn.content,
                "audio_url": turn.audio_url,
                "translated_content": turn.translated_content,
                "is_hint_used": turn.is_hint_used,
                "created_at": now,
                "updated_at": now,
            }
        )

    def list_by_session(self, session_id: str) -> List[Turn]:
        response = self._table.query(
            KeyConditionExpression=Key("PK").eq(f"SESSION#{session_id}") & Key("SK").begins_with("TURN#"),
            ScanIndexForward=True,
        )
        turns = [self._to_entity(item) for item in response.get("Items", [])]
        return sorted(turns, key=lambda item: item.turn_index)

    def delete_by_session(self, session_id: str) -> None:
        response = self._table.query(
            KeyConditionExpression=Key("PK").eq(f"SESSION#{session_id}") & Key("SK").begins_with("TURN#"),
        )
        with self._table.batch_writer() as batch:
            for item in response.get("Items", []):
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

    def _to_entity(self, item: dict) -> Turn:
        return Turn(
            session_id=item.get("session_id", ""),
            turn_index=int(item.get("turn_index", 0)),
            speaker=Speaker(item.get("speaker", Speaker.AI.value)),
            content=item.get("content", ""),
            audio_url=item.get("audio_url", ""),
            translated_content=item.get("translated_content", ""),
            is_hint_used=item.get("is_hint_used", False),
        )
