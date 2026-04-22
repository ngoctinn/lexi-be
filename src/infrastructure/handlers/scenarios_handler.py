import json

from infrastructure.persistence.static_scenario_repo import StaticScenarioRepository


SCENARIO_METADATA = {
    "s1": {"difficulty_level": "A1", "order": 1},
    "s1_2": {"difficulty_level": "A1", "order": 2},
    "s1_3": {"difficulty_level": "A1", "order": 3},
    "s1_4": {"difficulty_level": "A1", "order": 4},
    "s1_5": {"difficulty_level": "A1", "order": 5},
    "s1_6": {"difficulty_level": "A1", "order": 6},
    "s1_7": {"difficulty_level": "A1", "order": 7},
    "s2": {"difficulty_level": "A2", "order": 8},
    "s3": {"difficulty_level": "A2", "order": 9},
    "s4": {"difficulty_level": "B1", "order": 10},
    "s5": {"difficulty_level": "B1", "order": 11},
    "s6": {"difficulty_level": "B2", "order": 12},
    "s7": {"difficulty_level": "C1", "order": 13},
    "s8": {"difficulty_level": "C2", "order": 14},
}


def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def _scenario_to_payload(scenario):
    scenario_id = str(scenario.scenario_id)
    metadata = SCENARIO_METADATA.get(scenario_id, {})
    roles: list[str] = []

    for role in [
        *scenario.user_roles,
        *scenario.ai_roles,
        scenario.my_character,
        scenario.ai_character,
    ]:
        cleaned = str(role).strip()
        if cleaned and cleaned not in roles:
            roles.append(cleaned)

    return {
        "scenario_id": scenario_id,
        "scenario_title": scenario.scenario_title,
        "context": scenario.context,
        "roles": roles,
        "goals": list(scenario.goals),
        "is_active": scenario.is_active,
        "usage_count": scenario.usage_count,
        "difficulty_level": metadata.get("difficulty_level"),
        "order": metadata.get("order"),
    }


def handler(event, context):
    repository = StaticScenarioRepository()
    scenarios = sorted(
        repository.list_active(),
        key=lambda item: SCENARIO_METADATA.get(str(item.scenario_id), {}).get("order", 999),
    )

    return _response(
        200,
        {
            "success": True,
            "scenarios": [_scenario_to_payload(scenario) for scenario in scenarios],
        },
    )
