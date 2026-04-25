#!/usr/bin/env python3
"""
Test Bedrock API in Production
Test conversation endpoint to verify Bedrock is being called
"""

import json
import requests
import boto3
from datetime import datetime

# Stack outputs
API_URL = "https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod"
USER_POOL_ID = "ap-southeast-1_VhFl3NxNy"
CLIENT_ID = "4krhiauplon0iei1f5r4cgpq7i"
REGION = "ap-southeast-1"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log(msg, level='INFO'):
    ts = datetime.now().strftime('%H:%M:%S')
    if level == 'SUCCESS':
        print(f"{Colors.GREEN}[{ts}] ✅ {msg}{Colors.RESET}")
    elif level == 'ERROR':
        print(f"{Colors.RED}[{ts}] ❌ {msg}{Colors.RESET}")
    elif level == 'INFO':
        print(f"{Colors.BLUE}[{ts}] ℹ {msg}{Colors.RESET}")
    elif level == 'WARN':
        print(f"{Colors.YELLOW}[{ts}] ⚠ {msg}{Colors.RESET}")

def get_test_user_token():
    """Get JWT token for test user"""
    log("Getting test user token from Cognito...")
    
    cognito = boto3.client('cognito-idp', region_name=REGION)
    
    # List users to get a test user
    try:
        response = cognito.list_users(UserPoolId=USER_POOL_ID, Limit=1)
        if response['Users']:
            username = response['Users'][0]['Username']
            log(f"Found test user: {username}")
            return username
    except Exception as e:
        log(f"Error listing users: {e}", 'ERROR')
    
    return None

def test_conversation_endpoint(user_id, session_id, message):
    """Test conversation endpoint"""
    log(f"Testing conversation endpoint...")
    log(f"  User ID: {user_id}")
    log(f"  Session ID: {session_id}")
    log(f"  Message: {message}")
    
    url = f"{API_URL}/sessions/{session_id}/turns"
    
    # Create request body
    body = {
        "user_message": message,
        "audio_url": None
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_id}"  # Simplified for testing
    }
    
    try:
        response = requests.post(url, json=body, headers=headers, timeout=30)
        
        log(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            log(f"Response received", 'SUCCESS')
            
            # Check if response is from Bedrock or fallback
            ai_response = data.get('ai_response', '')
            
            if "Thanks. Could you say a bit more about that?" in ai_response:
                log(f"⚠️  Got FALLBACK response (not from Bedrock)", 'WARN')
                log(f"Response: {ai_response}")
                return False
            else:
                log(f"✅ Got REAL Bedrock response!", 'SUCCESS')
                log(f"Response: {ai_response[:200]}...")
                return True
        else:
            log(f"Error: {response.status_code}", 'ERROR')
            log(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        log(f"Error: {type(e).__name__}: {str(e)}", 'ERROR')
        return False

def main():
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"Bedrock Production Test")
    print(f"API: {API_URL}")
    print(f"Region: {REGION}")
    print(f"{'='*60}{Colors.RESET}\n")
    
    # For testing, we'll use a hardcoded user ID (from Cognito)
    # In production, you'd get this from authentication
    test_user_id = "test-user-123"
    test_session_id = "session-123"
    
    log("Starting Bedrock production test...")
    
    # Test 1: Simple greeting
    log("\n--- Test 1: Simple Greeting ---")
    result1 = test_conversation_endpoint(test_user_id, test_session_id, "Hello, how are you?")
    
    # Test 2: More complex message
    log("\n--- Test 2: Complex Message ---")
    result2 = test_conversation_endpoint(test_user_id, test_session_id, "I'm preparing for a business meeting tomorrow")
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}{Colors.RESET}")
    
    if result1 and result2:
        log("✅ All tests passed! Bedrock is working correctly!", 'SUCCESS')
        return 0
    else:
        log("❌ Some tests failed. Check logs above.", 'ERROR')
        return 1

if __name__ == "__main__":
    exit(main())
