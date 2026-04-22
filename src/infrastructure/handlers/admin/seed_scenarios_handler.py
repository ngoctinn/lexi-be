"""
Lambda handler để seed 14 scenarios từ StaticScenarioRepository vào DynamoDB.
Chạy một lần sau khi deploy. Idempotent — skip nếu scenario đã tồn tại.
"""
from datetime import datetime, timezone
from infrastructure.persistence.dynamo_scenario_repo import DynamoScenarioRepository
from infrastructure.persistence.static_scenario_repo import StaticScenarioRepository

# Mapping difficulty_level và order từ scenarios_handler.py cũ
_SCENARIO_METADATA = {
    "s1":   {"difficulty_level": "A1", "order": 1},
    "s1_2": {"difficulty_level": "A1", "order": 2},
    "s1_3": {"difficulty_level": "A1", "order": 3},
    "s1_4": {"difficulty_level": "A1", "order": 4},
    "s1_5": {"difficulty_level": "A1", "order": 5},
    "s1_6": {"difficulty_level": "A1", "order": 6},
    "s1_7": {"difficulty_level": "A1", "order": 7},
    "s2":   {"difficulty_level": "A2", "order": 8},
    "s3":   {"difficulty_level": "A2", "order": 9},
    "s4":   {"difficulty_level": "B1", "order": 10},
    "s5":   {"difficulty_level": "B1", "order": 11},
    "s6":   {"difficulty_level": "B2", "order": 12},
    "s7":   {"difficulty_level": "C1", "order": 13},
    "s8":   {"difficulty_level": "C2", "order": 14},
}


def handler(event, context):
    """Seed 14 scenarios vào DynamoDB. Idempotent."""
    static_repo = StaticScenarioRepository()
    dynamo_repo = DynamoScenarioRepository()

    scenarios = static_repo.list_all()
    now = datetime.now(timezone.utc).isoformat()
    seeded = 0
    skipped = 0

    for scenario in scenarios:
        meta = _SCENARIO_METADATA.get(str(scenario.scenario_id), {})
        scenario.difficulty_level = meta.get("difficulty_level", "")
        scenario.order = meta.get("order", 0)
        scenario.created_at = now
        scenario.updated_at = now

        # create() skip nếu đã tồn tại (idempotent)
        existing = dynamo_repo.get_by_id(str(scenario.scenario_id))
        if existing:
            skipped += 1
            continue

        dynamo_repo.create(scenario)
        seeded += 1

    return {
        "statusCode": 200,
        "body": f"Seeded {seeded} scenarios, skipped {skipped} existing.",
    }
