#!/usr/bin/env python3
"""
Fix context field for all scenarios to use predefined context categories
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set table name
os.environ['LEXI_TABLE_NAME'] = 'LexiApp'

# Predefined context categories
ENGLISH_SCENARIO_CONTEXTS = [
    "Social Communication",
    "At the Coffee Shop", 
    "Transportation & Asking Directions",
    "Health & Medical",
    "Travel & Hotels",
    "Daily Life",
    "Finance & Banking",
    "Shopping",
    "Food & Restaurants",
    "Travel & Aviation",
    "Work & Career",
    "Office & Meetings",
    "Business & Presentations",
    "Society & World"
]

def fix_scenarios_context():
    """Fix context field for all scenarios."""
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('LexiApp')
    
    print("🔍 Getting all scenarios...")
    
    # Get all scenarios
    response = table.query(
        IndexName='GSI3-Admin-EntityList',
        KeyConditionExpression='EntityType = :et',
        ExpressionAttributeValues={':et': 'SCENARIO'}
    )
    
    scenarios = response['Items']
    print(f"📊 Found {len(scenarios)} scenarios to fix")
    
    # Mapping scenario IDs to appropriate contexts
    context_mapping = {
        # Social & Communication
        'a1-greeting-introduction': 'Social Communication',
        'a2-making-plans': 'Social Communication',
        'b2-cultural-exchange': 'Social Communication',
        'a2-phone-conversation': 'Social Communication',
        
        # Food & Restaurants
        'a1-restaurant-ordering': 'Food & Restaurants',
        
        # Shopping
        'a1-shopping-basics': 'Shopping',
        
        # Health & Medical
        'a2-doctor-appointment': 'Health & Medical',
        
        # Travel & Hotels
        'a2-hotel-checkin': 'Travel & Hotels',
        'b1-travel-problem': 'Travel & Aviation',
        
        # Transportation & Directions
        'a1-asking-directions': 'Transportation & Asking Directions',
        
        # Work & Career
        'b1-job-interview': 'Work & Career',
        
        # Business & Presentations
        'b2-business-meeting': 'Business & Presentations',
        'b2-presentation-feedback': 'Business & Presentations',
        
        # Office & Meetings
        'c1-academic-discussion': 'Office & Meetings',
        'c1-media-interview': 'Office & Meetings',
        
        # Daily Life
        'b1-apartment-viewing': 'Daily Life',
        'b1-complaint-resolution': 'Daily Life',
        
        # Society & World
        'b2-debate-discussion': 'Society & World',
        'c1-crisis-management': 'Society & World',
        'c1-policy-debate': 'Society & World',
        'c2-diplomatic-negotiation': 'Society & World',
        'c2-literary-analysis': 'Society & World',
        'c2-scientific-symposium': 'Society & World',
        'c2-philosophical-debate': 'Society & World'
    }
    
    # Update each scenario
    updated_count = 0
    failed_count = 0
    
    for item in scenarios:
        try:
            scenario_id = item.get('scenario_id', '')
            
            # Get appropriate context
            new_context = context_mapping.get(scenario_id, 'Daily Life')  # Default to Daily Life
            
            # Update the item
            table.update_item(
                Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                },
                UpdateExpression="SET #c = :context",
                ExpressionAttributeNames={
                    '#c': 'context'
                },
                ExpressionAttributeValues={
                    ':context': new_context
                }
            )
            
            updated_count += 1
            print(f"✅ Fixed: {scenario_id} → {new_context}")
            
        except ClientError as e:
            failed_count += 1
            print(f"❌ Failed to fix {item.get('scenario_id', item.get('PK'))}: {e}")
    
    print(f"\n📈 Summary:")
    print(f"  ✅ Updated: {updated_count}")
    print(f"  ❌ Failed: {failed_count}")
    
    # Show context distribution
    print(f"\n📊 Context distribution:")
    context_counts = {}
    for scenario_id, context in context_mapping.items():
        context_counts[context] = context_counts.get(context, 0) + 1
    
    for context, count in sorted(context_counts.items()):
        print(f"  {context}: {count} scenarios")

if __name__ == "__main__":
    fix_scenarios_context()