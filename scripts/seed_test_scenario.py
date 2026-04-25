#!/usr/bin/env python3
"""Seed a test scenario for production testing."""

import boto3
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
table = dynamodb.Table('LexiApp')

def seed_scenario():
    """Create a test scenario."""
    scenario_id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"  # Fixed ULID for testing
    now = datetime.now(timezone.utc).isoformat()
    
    item = {
        'PK': f'SCENARIO#{scenario_id}',
        'SK': f'SCENARIO#{scenario_id}',
        'scenario_id': scenario_id,
        'scenario_title': 'Restaurant Ordering',
        'context': 'restaurant',
        'roles': ['customer', 'waiter'],
        'goals': ['order_food', 'ask_questions', 'make_requests'],
        'difficulty_level': 'B1',
        'is_active': True,
        'usage_count': 0,
        'created_at': now,
        'updated_at': now,
    }
    
    try:
        table.put_item(Item=item)
        print(f"✅ Created scenario: {scenario_id} - Restaurant Ordering")
        return scenario_id
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    seed_scenario()
