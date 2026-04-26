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
                # Metrics (Phase 5)
                "ttft_ms": turn.ttft_ms,
                "latency_ms": turn.latency_ms,
                "input_tokens": turn.input_tokens,
                "output_tokens": turn.output_tokens,
                "cost_usd": turn.cost_usd,
                "delivery_cue": turn.delivery_cue,
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
        from decimal import Decimal
        from ulid import ULID
        
        # Convert session_id from string to ULID
        session_id_str = item.get("session_id", "")
        try:
            session_id = ULID.from_str(session_id_str) if session_id_str else ULID()
        except (ValueError, TypeError):
            session_id = ULID()
        
        return Turn(
            session_id=session_id,
            turn_index=int(item.get("turn_index", 0)),
            speaker=Speaker(item.get("speaker", Speaker.AI.value)),
            content=item.get("content", ""),
            audio_url=item.get("audio_url", ""),
            translated_content=item.get("translated_content", ""),
            is_hint_used=item.get("is_hint_used", False),
            # Metrics (Phase 5) - DynamoDB returns Decimal, keep as Decimal
            ttft_ms=item.get("ttft_ms"),
            latency_ms=item.get("latency_ms"),
            input_tokens=int(item.get("input_tokens", 0)),
            output_tokens=int(item.get("output_tokens", 0)),
            cost_usd=item.get("cost_usd") or Decimal("0.0"),
            delivery_cue=item.get("delivery_cue", ""),
        )
