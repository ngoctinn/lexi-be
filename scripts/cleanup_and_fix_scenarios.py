#!/usr/bin/env python3
"""
1. Delete 5 new scenarios (created by our seed script)
2. Fix EntityType for 24 old scenarios from 'Scenario' to 'SCENARIO'
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set table name
os.environ['LEXI_TABLE_NAME'] = 'LexiApp'

def cleanup_and_fix_scenarios():
    """Delete new scenarios and fix old ones."""
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('LexiApp')
    
    print("🗑️ Step 1: Deleting 5 new scenarios...")
    
    # List of new scenarios to delete (created by our seed script)
    new_scenarios_to_delete = [
        'restaurant-ordering',
        'hotel-check-in', 
        'job-interview',
        'airport-check-in',
        'doctor-appointment'
    ]
    
    deleted_count = 0
    for scenario_id in new_scenarios_to_delete:
        try:
            table.delete_item(
                Key={
                    'PK': f'SCENARIO#{scenario_id}',
                    'SK': 'METADATA'
                }
            )
            deleted_count += 1
            print(f"🗑️ Deleted: {scenario_id}")
            
        except ClientError as e:
            print(f"❌ Failed to delete {scenario_id}: {e}")
    
    print(f"✅ Deleted {deleted_count} new scenarios")
    
    print(f"\n🔧 Step 2: Fixing EntityType for old scenarios...")
    
    # Scan for old scenarios with EntityType = 'Scenario'
    response = table.scan(
        FilterExpression="contains(PK, :scenario) AND EntityType = :old_type",
        ExpressionAttributeValues={
            ':scenario': 'SCENARIO#',
            ':old_type': 'Scenario'
        }
    )
    
    old_scenarios = response['Items']
    print(f"📊 Found {len(old_scenarios)} old scenarios to fix")
    
    # Update each old scenario
    updated_count = 0
    failed_count = 0
    
    for item in old_scenarios:
        try:
            # Update EntityType from 'Scenario' to 'SCENARIO'
            table.update_item(
                Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                },
                UpdateExpression="SET EntityType = :new_type",
                ExpressionAttributeValues={
                    ':new_type': 'SCENARIO'
                }
            )
            
            updated_count += 1
            print(f"🔧 Fixed: {item.get('scenario_id', item['PK'])}")
            
        except ClientError as e:
            failed_count += 1
            print(f"❌ Failed to fix {item.get('scenario_id', item['PK'])}: {e}")
    
    print(f"\n📈 Summary:")
    print(f"  🗑️ Deleted new scenarios: {deleted_count}")
    print(f"  🔧 Fixed old scenarios: {updated_count}")
    print(f"  ❌ Failed updates: {failed_count}")
    
    # Verify the final result
    print(f"\n🔍 Verifying final result...")
    
    # Count scenarios with correct EntityType
    response = table.query(
        IndexName='GSI3-Admin-EntityList',
        KeyConditionExpression='EntityType = :et',
        ExpressionAttributeValues={':et': 'SCENARIO'},
        Select='COUNT'
    )
    
    final_count = response['Count']
    print(f"📊 Total scenarios with EntityType='SCENARIO': {final_count}")
    
    if final_count == 24:
        print("🎉 Perfect! Now have 24 scenarios with correct EntityType")
    else:
        print(f"⚠️ Expected 24 scenarios, but found {final_count}")

if __name__ == "__main__":
    cleanup_and_fix_scenarios()