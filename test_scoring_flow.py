#!/usr/bin/env python3
"""Test complete session + scoring flow."""

import requests
import json
import time

# Read token
with open('id_token.txt', 'r') as f:
    token = f.read().strip()

BASE_URL = "https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod"  # Production API
HEADERS = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("=" * 60)
print("TEST: Complete Session + Scoring Flow")
print("=" * 60)

# Step 1: Create session
print("\n[1] Creating session...")
create_payload = {
    "scenario_id": "restaurant-ordering",
    "level": "B1",
    "learner_role_id": "customer",
    "ai_role_id": "waiter",
    "ai_character": "Sarah",
    "selected_goal": "order food"
}

response = requests.post(
    f"{BASE_URL}/sessions",
    json=create_payload,
    headers=HEADERS
)

if response.status_code not in [200, 201]:
    print(f"❌ Create session failed: {response.status_code}")
    print(response.text)
    exit(1)

session_data = response.json()
session_id = session_data["data"]["session_id"]
print(f"✅ Session created: {session_id}")

# Step 2: Submit a turn
print("\n[2] Submitting user turn...")
turn_payload = {
    "text": "I would like to order a coffee and a sandwich please"
}

response = requests.post(
    f"{BASE_URL}/sessions/{session_id}/turns",
    json=turn_payload,
    headers=HEADERS
)

if response.status_code != 200:
    print(f"❌ Submit turn failed: {response.status_code}")
    print(response.text)
    exit(1)

print(f"✅ Turn submitted")

# Step 3: Complete session (triggers scoring)
print("\n[3] Completing session (triggers scoring)...")
time.sleep(1)  # Wait a bit

response = requests.post(
    f"{BASE_URL}/sessions/{session_id}/complete",
    headers=HEADERS
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    data = response.json()
    if "data" in data and "scoring" in data["data"]:
        scoring = data["data"]["scoring"]
        print(f"\n✅ Scoring successful!")
        print(f"  - Overall: {scoring.get('overall_score', 'N/A')}")
        print(f"  - Fluency: {scoring.get('fluency_score', 'N/A')}")
        print(f"  - Grammar: {scoring.get('grammar_score', 'N/A')}")
        print(f"  - Feedback: {scoring.get('feedback', 'N/A')[:100]}...")
    else:
        print(f"❌ No scoring in response")
else:
    print(f"❌ Complete session failed: {response.status_code}")

print("\n" + "=" * 60)
