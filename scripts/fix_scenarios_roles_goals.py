#!/usr/bin/env python3
"""
Fix old scenarios:
1. Add missing 'roles' field (2 roles per scenario)
2. Shorten 'goals' from long sentences to short phrases
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set table name
os.environ['LEXI_TABLE_NAME'] = 'LexiApp'

def fix_scenarios_roles_and_goals():
    """Fix roles and goals for all scenarios."""
    
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
    
    # Mapping for roles based on scenario context/title
    roles_mapping = {
        'restaurant': ['customer', 'waiter'],
        'hotel': ['guest', 'receptionist'], 
        'doctor': ['patient', 'doctor'],
        'shopping': ['customer', 'cashier'],
        'job': ['candidate', 'interviewer'],
        'phone': ['caller', 'receiver'],
        'apartment': ['tenant', 'landlord'],
        'complaint': ['customer', 'manager'],
        'travel': ['traveler', 'agent'],
        'greeting': ['person A', 'person B'],
        'directions': ['tourist', 'local'],
        'plans': ['friend A', 'friend B'],
        'business': ['negotiator A', 'negotiator B'],
        'presentation': ['presenter', 'audience'],
        'debate': ['debater A', 'debater B'],
        'cultural': ['person A', 'person B'],
        'academic': ['researcher A', 'researcher B'],
        'crisis': ['manager', 'team member'],
        'policy': ['policymaker', 'advisor'],
        'literary': ['critic A', 'critic B'],
        'media': ['interviewer', 'interviewee'],
        'diplomatic': ['diplomat A', 'diplomat B'],
        'scientific': ['scientist A', 'scientist B'],
        'philosophical': ['philosopher A', 'philosopher B']
    }
    
    # Function to determine roles from scenario_id
    def get_roles(scenario_id):
        for key, roles in roles_mapping.items():
            if key in scenario_id:
                return roles
        return ['person A', 'person B']  # default
    
    # Function to shorten goals
    def shorten_goals(goals_list):
        shortened = []
        for goal in goals_list:
            # Extract key action words from long sentences
            goal_text = goal.lower()
            
            if 'order' in goal_text and 'food' in goal_text:
                shortened.append('order food')
            elif 'ask' in goal_text and 'menu' in goal_text:
                shortened.append('ask about menu')
            elif 'request' in goal_text and ('bill' in goal_text or 'check' in goal_text):
                shortened.append('request bill')
            elif 'introduce' in goal_text:
                shortened.append('introduce yourself')
            elif 'book' in goal_text or 'reservation' in goal_text:
                shortened.append('make reservation')
            elif 'check' in goal_text and 'in' in goal_text:
                shortened.append('check in')
            elif 'amenities' in goal_text:
                shortened.append('ask about amenities')
            elif 'appointment' in goal_text:
                shortened.append('schedule appointment')
            elif 'symptoms' in goal_text:
                shortened.append('describe symptoms')
            elif 'treatment' in goal_text:
                shortened.append('discuss treatment')
            elif 'prescription' in goal_text:
                shortened.append('get prescription')
            elif 'directions' in goal_text:
                shortened.append('ask directions')
            elif 'price' in goal_text or 'cost' in goal_text:
                shortened.append('ask about price')
            elif 'complaint' in goal_text:
                shortened.append('make complaint')
            elif 'solution' in goal_text:
                shortened.append('find solution')
            elif 'negotiate' in goal_text:
                shortened.append('negotiate terms')
            elif 'present' in goal_text:
                shortened.append('give presentation')
            elif 'question' in goal_text:
                shortened.append('answer questions')
            elif 'discuss' in goal_text:
                shortened.append('discuss topic')
            elif 'analyze' in goal_text:
                shortened.append('analyze situation')
            elif 'propose' in goal_text:
                shortened.append('propose solution')
            elif 'coordinate' in goal_text:
                shortened.append('coordinate response')
            elif 'communicate' in goal_text:
                shortened.append('communicate effectively')
            else:
                # Fallback: take first 2-3 words
                words = goal.split()[:3]
                shortened.append(' '.join(words).lower().rstrip('.,!?'))
        
        # Ensure we have 2-4 goals, remove duplicates
        shortened = list(dict.fromkeys(shortened))  # Remove duplicates while preserving order
        return shortened[:4] if len(shortened) > 4 else shortened
    
    # Update each scenario
    updated_count = 0
    failed_count = 0
    
    for item in scenarios:
        try:
            scenario_id = item.get('scenario_id', '')
            
            # Determine roles
            roles = get_roles(scenario_id)
            
            # Shorten goals
            goals_field = item.get('goals', [])
            if isinstance(goals_field, dict) and 'L' in goals_field:
                # DynamoDB format: {'L': [{'S': 'goal1'}, {'S': 'goal2'}]}
                current_goals = [goal['S'] for goal in goals_field['L']]
            elif isinstance(goals_field, list):
                # Already in list format
                current_goals = goals_field
            else:
                current_goals = []
            
            shortened_goals = shorten_goals(current_goals)
            
            # Update the item
            table.update_item(
                Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                },
                UpdateExpression="SET #r = :roles, #g = :goals",
                ExpressionAttributeNames={
                    '#r': 'roles',
                    '#g': 'goals'
                },
                ExpressionAttributeValues={
                    ':roles': roles,
                    ':goals': shortened_goals
                }
            )
            
            updated_count += 1
            print(f"✅ Fixed: {scenario_id}")
            print(f"   Roles: {roles}")
            print(f"   Goals: {shortened_goals}")
            
        except ClientError as e:
            failed_count += 1
            print(f"❌ Failed to fix {item.get('scenario_id', item.get('PK'))}: {e}")
    
    print(f"\n📈 Summary:")
    print(f"  ✅ Updated: {updated_count}")
    print(f"  ❌ Failed: {failed_count}")

if __name__ == "__main__":
    fix_scenarios_roles_and_goals()