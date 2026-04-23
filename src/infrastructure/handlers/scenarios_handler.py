import json

from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
from shared.http_utils import dumps


def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": dumps(body),
    }


def _scenario_to_payload(scenario):
    return {
        "scenario_id": str(scenario.scenario_id),
        "scenario_title": scenario.scenario_title,
        "context": scenario.context,
        "roles": list(scenario.roles),
        "goals": list(scenario.goals),
        "is_active": scenario.is_active,
        "usage_count": scenario.usage_count,
        "difficulty_level": scenario.difficulty_level,
        "order": scenario.order,
    }


def handler(event, context):
    repository = DynamoScenarioRepository()
    scenarios = sorted(
        repository.list_active(),
        key=lambda item: item.order,
    )

    return _response(
        200,
        {
            "success": True,
            "scenarios": [_scenario_to_payload(scenario) for scenario in scenarios],
        },
    )
