import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from infrastructure.handlers.scenarios_handler import handler


def test_scenarios_handler_returns_active_scenarios():
    # Mock DynamoDB table and environment
    with patch.dict(os.environ, {"LEXI_TABLE_NAME": "test-table"}):
        with patch("infrastructure.persistence.dynamo_scenario_repo.boto3.resource") as mock_boto3:
            # Mock DynamoDB table
            mock_table = MagicMock()
            mock_boto3.return_value.Table.return_value = mock_table
            
            # Mock scenario data
            from domain.entities.scenario import Scenario
            from ulid import ULID
            
            test_scenario = Scenario(
                scenario_id=ULID(),
                scenario_title="Test Scenario",
                context="Test context",
                roles=["Role1", "Role2"],
                goals=["Goal1"],
                is_active=True,
                usage_count=0,
                difficulty_level="B1",
                order=1,
            )
            
            # Mock repository list_active method
            with patch("infrastructure.persistence.dynamo_scenario_repo.DynamoScenarioRepository.list_active") as mock_list:
                mock_list.return_value = [test_scenario]
                
                response = handler({}, None)
                payload = json.loads(response["body"])

                assert response["statusCode"] == 200
                assert payload["success"] is True
                assert len(payload["scenarios"]) == 1
                assert payload["scenarios"][0]["scenario_title"] == "Test Scenario"
