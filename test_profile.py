#!/usr/bin/env python3
"""Test GET /profile endpoint."""

import requests
import json

# Read token
with open('id_token.txt', 'r') as f:
    token = f.read().strip()

BASE_URL = "https://yz8fyx7zub.execute-api.ap-southeast-1.amazonaws.com/Prod"
HEADERS = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("=" * 60)
print("TEST: GET /profile")
print("=" * 60)

response = requests.get(
    f"{BASE_URL}/profile",
    headers=HEADERS
)

print(f"\nStatus: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Body: {response.text}")

if response.status_code == 200:
    data = response.json()
    print(f"\n✅ Profile retrieved successfully!")
    print(f"Response: {json.dumps(data, indent=2)}")
else:
    print(f"\n❌ Failed to get profile")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

print("\n" + "=" * 60)
