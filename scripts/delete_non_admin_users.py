#!/usr/bin/env python3
"""
Script to delete all non-admin users from Cognito and DynamoDB
Keeps only the admin user (admin@ngoctin.me)
"""

import boto3
import json
from typing import List, Dict

# Initialize AWS clients
cognito = boto3.client('cognito-idp', region_name='ap-southeast-1')
dynamodb = boto3.client('dynamodb', region_name='ap-southeast-1')

USER_POOL_ID = 'ap-southeast-1_I9ri7n518'
TABLE_NAME = 'LexiApp'
ADMIN_USER_ID = '99ba055c-70f1-7049-aed3-d14c9c988657'

def get_all_user_data(user_id: str) -> List[Dict]:
    """Get all DynamoDB items for a user"""
    items = []
    
    # Get profile
    try:
        response = dynamodb.query(
            TableName=TABLE_NAME,
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': {'S': f'USER#{user_id}'}}
        )
        items.extend(response.get('Items', []))
    except Exception as e:
        print(f"  Error querying USER items: {e}")
    
    # Get flashcards
    try:
        response = dynamodb.query(
            TableName=TABLE_NAME,
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': {'S': f'FLASHCARD#{user_id}'}}
        )
        items.extend(response.get('Items', []))
    except Exception as e:
        print(f"  Error querying FLASHCARD items: {e}")
    
    # Scan for sessions and other data
    try:
        response = dynamodb.scan(
            TableName=TABLE_NAME,
            FilterExpression='contains(PK, :user_id) OR contains(user_id, :user_id)',
            ExpressionAttributeValues={':user_id': {'S': user_id}}
        )
        items.extend(response.get('Items', []))
    except Exception as e:
        print(f"  Error scanning for user data: {e}")
    
    # Remove duplicates based on PK and SK
    unique_items = {}
    for item in items:
        key = (item['PK']['S'], item['SK']['S'])
        unique_items[key] = item
    
    return list(unique_items.values())

def delete_dynamodb_items(items: List[Dict]):
    """Delete items from DynamoDB"""
    for item in items:
        try:
            dynamodb.delete_item(
                TableName=TABLE_NAME,
                Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                }
            )
            print(f"  ✓ Deleted: {item['PK']['S']} / {item['SK']['S']}")
        except Exception as e:
            print(f"  ✗ Error deleting {item['PK']['S']}/{item['SK']['S']}: {e}")

def delete_user(email: str, user_id: str):
    """Delete a user from Cognito and DynamoDB"""
    print(f"\n🗑️  Deleting user: {email} ({user_id})")
    
    # 1. Get all DynamoDB data
    print("  📊 Fetching DynamoDB data...")
    items = get_all_user_data(user_id)
    print(f"  Found {len(items)} items to delete")
    
    # 2. Delete from DynamoDB
    if items:
        print("  🗄️  Deleting from DynamoDB...")
        delete_dynamodb_items(items)
    
    # 3. Delete from Cognito
    print("  👤 Deleting from Cognito...")
    try:
        cognito.admin_delete_user(
            UserPoolId=USER_POOL_ID,
            Username=email
        )
        print(f"  ✓ Deleted from Cognito")
    except Exception as e:
        print(f"  ✗ Error deleting from Cognito: {e}")
    
    print(f"✅ User {email} deleted successfully")

def main():
    # Users to delete (all except admin)
    users_to_delete = [
        ('tinvg2918@gmail.com', 'f96a751c-40b1-70bd-865b-7340c53f06a0'),
        ('ngoctin.work@gmail.com', '39aa15cc-30c1-70ce-b76b-df5a23b0b01b'),
        ('tinn3941@gmail.com', '19bad57c-c051-707d-b1b0-d386dd7592b6'),
    ]
    
    print("=" * 60)
    print("🚨 DELETE NON-ADMIN USERS")
    print("=" * 60)
    print(f"Keeping admin user: admin@ngoctin.me ({ADMIN_USER_ID})")
    print(f"Deleting {len(users_to_delete)} users...")
    
    for email, user_id in users_to_delete:
        delete_user(email, user_id)
    
    print("\n" + "=" * 60)
    print("✅ ALL NON-ADMIN USERS DELETED")
    print("=" * 60)

if __name__ == '__main__':
    main()
