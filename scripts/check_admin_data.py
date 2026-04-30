#!/usr/bin/env python3
"""
Script to check if there's any data in DynamoDB for admin endpoints
"""
import boto3
import os
from decimal import Decimal

# Get table name from environment or use default
TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'LexiApp')

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
table = dynamodb.Table(TABLE_NAME)

print(f"Checking table: {TABLE_NAME}\n")

# Check users
print("=" * 50)
print("CHECKING USERS")
print("=" * 50)

try:
    # Scan for all user profiles
    response = table.scan(
        FilterExpression='begins_with(PK, :pk) AND SK = :sk',
        ExpressionAttributeValues={
            ':pk': 'USER#',
            ':sk': 'PROFILE'
        }
    )
    
    users = response.get('Items', [])
    print(f"Found {len(users)} users\n")
    
    for user in users:
        print(f"User ID: {user.get('PK')}")
        print(f"  Email: {user.get('email')}")
        print(f"  Display Name: {user.get('display_name')}")
        print(f"  Role: {user.get('role')}")
        print(f"  Active: {user.get('is_active')}")
        print()
        
except Exception as e:
    print(f"Error checking users: {e}\n")

# Check scenarios
print("=" * 50)
print("CHECKING SCENARIOS")
print("=" * 50)

try:
    # Scan for all scenarios
    response = table.scan(
        FilterExpression='begins_with(PK, :pk)',
        ExpressionAttributeValues={
            ':pk': 'SCENARIO#'
        }
    )
    
    scenarios = response.get('Items', [])
    print(f"Found {len(scenarios)} scenarios\n")
    
    for scenario in scenarios:
        print(f"Scenario ID: {scenario.get('PK')}")
        print(f"  Title: {scenario.get('scenario_title')}")
        print(f"  Active: {scenario.get('is_active')}")
        print(f"  Difficulty: {scenario.get('difficulty_level')}")
        print()
        
except Exception as e:
    print(f"Error checking scenarios: {e}\n")

print("=" * 50)
print("SUMMARY")
print("=" * 50)
print(f"Total Users: {len(users) if 'users' in locals() else 0}")
print(f"Total Scenarios: {len(scenarios) if 'scenarios' in locals() else 0}")
print()

if 'users' not in locals() or len(users) == 0:
    print("⚠️  No users found in database!")
    print("   This is why admin dashboard shows empty list.")
    print()
    
if 'scenarios' not in locals() or len(scenarios) == 0:
    print("⚠️  No scenarios found in database!")
    print("   Run: python scripts/seed_scenarios.py to add scenarios")
    print()
