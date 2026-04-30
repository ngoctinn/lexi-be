from datetime import datetime, timezone
from typing import List, Optional
import os
import logging

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from application.repositories.scenario_repository import ScenarioRepository
from domain.entities.scenario import Scenario

logger = logging.getLogger(__name__)


class DynamoScenarioRepository(ScenarioRepository):
    """Lưu trữ Scenario trong DynamoDB."""

    def __init__(self, table=None):
        # Use env var with fallback to empty string for local testing
        table_name = os.environ.get("LEXI_TABLE_NAME", "")
        if not table_name:
            # For local testing without DynamoDB, use empty table
            # This will cause validation error but won't crash the Lambda
            logger.warning("LEXI_TABLE_NAME not set, DynamoDB operations will fail")
        self._table = table or boto3.resource("dynamodb").Table(table_name) if table_name else None

    # --- Read operations ---

    def list_active(self) -> List[Scenario]:
        """Lấy tất cả scenario đang active — dùng cho Learner."""
        if not self._table:
            logger.error("DynamoDB table not initialized (LEXI_TABLE_NAME not set)")
            return []
        all_scenarios = self._query_gsi3()
        return [s for s in all_scenarios if s.is_active]

    def list_all(self) -> List[Scenario]:
        """Lấy tất cả scenario kể cả inactive — dùng cho Admin."""
        if not self._table:
            logger.error("DynamoDB table not initialized (LEXI_TABLE_NAME not set)")
            return []
        return self._query_gsi3()

    def get_by_id(self, scenario_id: str) -> Optional[Scenario]:
        """Lấy scenario theo ID."""
        response = self._table.get_item(
            Key={
                "PK": f"SCENARIO#{scenario_id}",
                "SK": "METADATA",
            }
        )
        item = response.get("Item")
        return self._to_entity(item) if item else None

    # --- Write operations ---

    def create(self, scenario: Scenario) -> None:
        """Tạo scenario mới — fail nếu đã tồn tại."""
        now = datetime.now(timezone.utc).isoformat()
        if not scenario.created_at:
            scenario.created_at = now
        if not scenario.updated_at:
            scenario.updated_at = now

        try:
            self._table.put_item(
                Item=self._to_item(scenario),
                ConditionExpression="attribute_not_exists(PK)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return  # Đã tồn tại — skip (idempotent seed)
            raise

    def save(self, scenario: Scenario) -> None:
        """Upsert scenario — dùng để tăng usage_count."""
        now = datetime.now(timezone.utc).isoformat()
        if not scenario.created_at:
            scenario.created_at = now
        scenario.updated_at = now
        self._table.put_item(Item=self._to_item(scenario))

    def update(self, scenario: Scenario) -> None:
        """Cập nhật scenario đã tồn tại."""
        scenario.updated_at = datetime.now(timezone.utc).isoformat()
        self._table.update_item(
            Key={
                "PK": f"SCENARIO#{scenario.scenario_id}",
                "SK": "METADATA",
            },
            UpdateExpression=(
                "SET scenario_title = :st, context = :ctx, #r = :roles, goals = :g, "
                "is_active = :ia, usage_count = :uc, difficulty_level = :dl, "
                "#ord = :o, notes = :n, updated_at = :ua"
            ),
            ExpressionAttributeNames={
                "#r": "roles",  # roles là reserved word
                "#ord": "order",  # order là reserved word
            },
            ExpressionAttributeValues={
                ":st": scenario.scenario_title,
                ":ctx": scenario.context,
                ":roles": scenario.roles,
                ":g": scenario.goals,
                ":ia": scenario.is_active,
                ":uc": scenario.usage_count,
                ":dl": scenario.difficulty_level,
                ":o": scenario.order,
                ":n": scenario.notes,
                ":ua": scenario.updated_at,
            },
        )

    # --- Private helpers ---

    def _query_gsi3(self) -> List[Scenario]:
        """Query GSI3 để lấy tất cả scenario."""
        response = self._table.query(
            IndexName="GSI3-Admin-EntityList",
            KeyConditionExpression=Key("EntityType").eq("SCENARIO"),
            ScanIndexForward=True,
        )
        return [self._to_entity(item) for item in response.get("Items", [])]

    def _to_item(self, scenario: Scenario) -> dict:
        return {
            "PK": f"SCENARIO#{scenario.scenario_id}",
            "SK": "METADATA",
            "EntityType": "SCENARIO",
            "created_at": scenario.created_at,
            "scenario_id": scenario.scenario_id,
            "scenario_title": scenario.scenario_title,
            "context": scenario.context,
            "roles": scenario.roles,
            "goals": scenario.goals,
            "is_active": scenario.is_active,
            "usage_count": scenario.usage_count,
            "difficulty_level": scenario.difficulty_level,
            "order": scenario.order,
            "notes": scenario.notes,
            "updated_at": scenario.updated_at,
        }

    def _to_entity(self, item: dict) -> Scenario:
        return Scenario(
            scenario_id=item.get("scenario_id", ""),
            scenario_title=item.get("scenario_title", ""),
            context=item.get("context", ""),
            roles=list(item.get("roles", [])),
            goals=list(item.get("goals", [])),
            is_active=item.get("is_active", True),
            usage_count=item.get("usage_count", 0),
            difficulty_level=item.get("difficulty_level", ""),
            order=item.get("order", 0),
            notes=item.get("notes", ""),
            created_at=item.get("created_at", ""),
            updated_at=item.get("updated_at", ""),
        )
