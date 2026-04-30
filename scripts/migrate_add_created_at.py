#!/usr/bin/env python3
"""
Migration script: Add created_at to existing user profiles.

This fixes GSI3-Admin-EntityList query which requires created_at as RANGE key.
For existing users, we use joined_at as created_at value.
"""

import boto3
from boto3.dynamodb.conditions import Key

def migrate():
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table('LexiApp')
    
    print("🔍 Scanning for user profiles without created_at...")
    
    # Scan for all USER# items with SK=PROFILE
    response = table.scan(
        FilterExpression='begins_with(PK, :pk) AND SK = :sk',
        ExpressionAttributeValues={
            ':pk': 'USER#',
            ':sk': 'PROFILE'
        }
    )
    
    items = response.get('Items', [])
    print(f"Found {len(items)} user profiles")
    
    updated_count = 0
    for item in items:
        user_id = item.get('user_id')
        has_created_at = 'created_at' in item
        
        if not has_created_at:
            # Use joined_at as created_at, or current time if joined_at doesn't exist
            created_at_value = item.get('joined_at', item.get('GSI1SK', '2026-04-30T00:00:00+00:00'))
            
            print(f"  Updating {user_id} (email: {item.get('email')})")
            print(f"    Setting created_at = {created_at_value}")
            
            table.update_item(
                Key={
                    'PK': f"USER#{user_id}",
                    'SK': 'PROFILE'
                },
                UpdateExpression='SET created_at = :ca',
                ExpressionAttributeValues={
                    ':ca': created_at_value
                }
            )
            updated_count += 1
        else:
            print(f"  ✓ {user_id} already has created_at")
    
    print(f"\n✅ Migration complete! Updated {updated_count} user profiles")
    
    # Verify GSI3 query works now
    print("\n🔍 Verifying GSI3 query...")
    response = table.query(
        IndexName='GSI3-Admin-EntityList',
        KeyConditionExpression=Key('EntityType').eq('USER_PROFILE'),
        Limit=5
    )
    
    count = response.get('Count', 0)
    print(f"✅ GSI3 query returned {count} user profiles")
    
    if count > 0:
        print("\nSample users:")
        for item in response.get('Items', []):
            print(f"  - {item.get('email')} (created_at: {item.get('created_at')})")

if __name__ == '__main__':
    migrate()
