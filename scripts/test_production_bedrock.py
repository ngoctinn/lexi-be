#!/usr/bin/env python3
"""
Test Bedrock integration on production AWS.
Creates a test user, gets token, and tests full flow.
"""

import json
import time
import boto3
import requests
from botocore.exceptions import ClientError

# AWS Configuration
REGION = "ap-southeast-1"
USER_POOL_ID = "ap-southeast-1_VhFl3NxNy"
CLIENT_ID = "4krhiauplon0iei1f5r4cgpq7i"
API_URL = "https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod"

# Test user credentials
TEST_EMAIL = "test-bedrock@lexi.dev"
TEST_PASSWORD = "TestPassword123!"

cognito = boto3.client('cognito-idp', region_name=REGION)

def create_or_get_test_user():
    """Create test user or get existing one."""
    print("\n🔍 Checking for test user...")
    
    try:
        # Try to create user
        response = cognito.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=TEST_EMAIL,
            UserAttributes=[
                {'Name': 'email', 'Value': TEST_EMAIL},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            MessageAction='SUPPRESS',
            TemporaryPassword=TEST_PASSWORD
        )
        print(f"✅ Created test user: {TEST_EMAIL}")
        
        # Set permanent password
        cognito.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=TEST_EMAIL,
            Password=TEST_PASSWORD,
            Permanent=True
        )
        print(f"✅ Set permanent password")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'UsernameExistsException':
            print(f"✅ Test user already exists: {TEST_EMAIL}")
        else:
            raise

def get_jwt_token():
    """Get JWT token for test user."""
    print("\n🔑 Getting JWT token...")
    
    try:
        response = cognito.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': TEST_EMAIL,
                'PASSWORD': TEST_PASSWORD
            }
        )
        
        token = response['AuthenticationResult']['IdToken']
        print(f"✅ Got JWT token (length: {len(token)})")
        return token
        
    except ClientError as e:
        print(f"❌ Failed to get token: {e}")
        raise

def test_list_scenarios():
    """Test public endpoint (no auth)."""
    print("\n" + "="*60)
    print("TEST 1: List Scenarios (Public)")
    print("="*60)
    
    response = requests.get(f"{API_URL}/scenarios")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('scenarios'):
            scenario = data['scenarios'][0]
            print(f"✅ Found scenario: {scenario['scenario_id']} - {scenario['scenario_title']}")
            return scenario['scenario_id']
        else:
            print("❌ No scenarios found")
            return None
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None

def test_create_session(token, scenario_id):
    """Test session creation."""
    print("\n" + "="*60)
    print("TEST 2: Create Session")
    print("="*60)
    
    payload = {
        "scenario_id": scenario_id,
        "learner_role_id": "customer",
        "ai_role_id": "waiter",
        "ai_gender": "female",
        "level": "B1",
        "selected_goals": ["order_food"]
    }
    
    response = requests.post(
        f"{API_URL}/sessions",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    if response.status_code == 201:
        data = response.json()
        session_id = data.get('session_id')
        print(f"✅ Session created: {session_id}")
        return session_id
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None

def test_submit_turn(token, session_id):
    """Test turn submission (triggers Bedrock Nova Micro)."""
    print("\n" + "="*60)
    print("TEST 3: Submit Turn (Bedrock Nova Micro)")
    print("="*60)
    
    payload = {
        "text": "Hello, I would like to order a coffee please.",
        "audio_url": "",
        "is_hint_used": False
    }
    
    print("📤 Sending user message...")
    start_time = time.time()
    
    response = requests.post(
        f"{API_URL}/sessions/{session_id}/turns",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    elapsed = (time.time() - start_time) * 1000
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('success'):
            ai_turn = data.get('ai_turn', {})
            session = data.get('session', {})
            
            print(f"✅ Turn submitted successfully")
            print(f"\n📊 Bedrock Response:")
            print(f"  Model: {session.get('assigned_model', 'N/A')}")
            print(f"  AI Text: {ai_turn.get('content', 'N/A')[:100]}...")
            print(f"  TTFT: {ai_turn.get('ttft_ms', 'N/A')}ms")
            print(f"  Latency: {ai_turn.get('latency_ms', 'N/A')}ms")
            print(f"  Output Tokens: {ai_turn.get('output_tokens', 'N/A')}")
            print(f"  Cost: ${ai_turn.get('cost_usd', 'N/A')}")
            print(f"  Total Request Time: {elapsed:.0f}ms")
            
            # Verify Nova Micro
            model = session.get('assigned_model', '')
            if 'nova-micro' in model.lower():
                print(f"\n✅ Confirmed: Using Nova Micro")
                return True
            else:
                print(f"\n⚠️  Warning: Not using Nova Micro (got: {model})")
                return False
        else:
            print(f"❌ Response indicates failure")
            print(json.dumps(data, indent=2))
            return False
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_complete_session(token, session_id):
    """Test session completion (triggers Bedrock scoring)."""
    print("\n" + "="*60)
    print("TEST 4: Complete Session (Bedrock Scoring)")
    print("="*60)
    
    response = requests.post(
        f"{API_URL}/sessions/{session_id}/complete",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('success'):
            scoring = data.get('scoring', {})
            
            print(f"✅ Session completed successfully")
            print(f"\n📊 Scoring (Nova Micro):")
            print(f"  Fluency: {scoring.get('fluency', 'N/A')}")
            print(f"  Pronunciation: {scoring.get('pronunciation', 'N/A')}")
            print(f"  Grammar: {scoring.get('grammar', 'N/A')}")
            print(f"  Vocabulary: {scoring.get('vocabulary', 'N/A')}")
            print(f"  Overall: {scoring.get('overall', 'N/A')}")
            print(f"  Feedback: {scoring.get('feedback', 'N/A')[:100]}...")
            
            return True
        else:
            print(f"❌ Response indicates failure")
            print(json.dumps(data, indent=2))
            return False
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def main():
    print("\n" + "="*60)
    print("PRODUCTION BEDROCK INTEGRATION TEST")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"Region: {REGION}")
    
    try:
        # Setup
        create_or_get_test_user()
        token = get_jwt_token()
        
        # Test flow
        scenario_id = test_list_scenarios()
        if not scenario_id:
            print("\n❌ Cannot proceed without scenario")
            return 1
        
        session_id = test_create_session(token, scenario_id)
        if not session_id:
            print("\n❌ Cannot proceed without session")
            return 1
        
        bedrock_ok = test_submit_turn(token, session_id)
        scoring_ok = test_complete_session(token, session_id)
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"List Scenarios: ✅ PASS")
        print(f"Create Session: ✅ PASS")
        print(f"Bedrock Response: {'✅ PASS' if bedrock_ok else '❌ FAIL'}")
        print(f"Bedrock Scoring: {'✅ PASS' if scoring_ok else '❌ FAIL'}")
        
        if bedrock_ok and scoring_ok:
            print("\n🎉 ALL TESTS PASSED")
            print("✅ Nova Micro is working correctly in production")
            return 0
        else:
            print("\n⚠️  SOME TESTS FAILED")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
