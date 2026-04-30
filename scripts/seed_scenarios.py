#!/usr/bin/env python3
"""
Script to seed scenarios into DynamoDB.
Usage: python scripts/seed_scenarios.py
"""
import json
import boto3
from datetime import datetime, timezone

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='ap-southeast-1')
TABLE_NAME = 'LexiApp'

def load_scenarios():
    """Load scenarios from JSON file."""
    with open('scripts/seed_scenarios.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def scenario_to_dynamodb_item(scenario):
    """Convert scenario dict to DynamoDB item format."""
    now = datetime.now(timezone.utc).isoformat()
    
    item = {
        'PK': {'S': f"SCENARIO#{scenario['scenario_id']}"},
        'SK': {'S': 'METADATA'},
        'EntityType': {'S': 'SCENARIO'},
        'scenario_id': {'S': scenario['scenario_id']},
        'scenario_title': {'S': scenario['scenario_title']},
        'context': {'S': scenario['context']},
        'roles': {'L': [{'S': role} for role in scenario['roles']]},
        'goals': {'L': [{'S': goal} for goal in scenario['goals']]},
        'difficulty_level': {'S': scenario['difficulty_level']},
        'order': {'N': str(scenario['order'])},
        'is_active': {'BOOL': scenario['is_active']},
        'usage_count': {'N': str(scenario.get('usage_count', 0))},
        'created_at': {'S': now},
        'updated_at': {'S': now},
    }
    
    # Add notes if present
    if 'notes' in scenario:
        item['notes'] = {'S': scenario['notes']}
    
    return item

def seed_scenarios():
    """Seed all scenarios into DynamoDB."""
    scenarios = load_scenarios()
    
    print(f"Loading {len(scenarios)} scenarios into DynamoDB...")
    
    success_count = 0
    error_count = 0
    
    for scenario in scenarios:
        try:
            item = scenario_to_dynamodb_item(scenario)
            dynamodb.put_item(
                TableName=TABLE_NAME,
                Item=item
            )
            print(f"✓ Inserted: {scenario['scenario_id']} - {scenario['scenario_title']}")
            success_count += 1
        except Exception as e:
            print(f"✗ Error inserting {scenario['scenario_id']}: {str(e)}")
            error_count += 1
    
    print(f"\n{'='*60}")
    print(f"Seeding completed!")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"{'='*60}")

if __name__ == '__main__':
    seed_scenarios()
