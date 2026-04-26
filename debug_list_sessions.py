#!/usr/bin/env python3
"""Debug script to test list_sessions directly"""
import sys
sys.path.insert(0, 'src')

from infrastructure.persistence.dynamo_session_repo import DynamoSessionRepo
from application.use_cases.speaking_session_use_cases import ListSpeakingSessionsUseCase
from infrastructure.persistence.dynamo_scoring_repo import DynamoScoringRepo
import os

os.environ['LEXI_TABLE_NAME'] = 'LexiApp'

user_id = "299a95fc-3021-7050-5812-42fffa4971ec"

# Test repository directly
print("=== Testing DynamoSessionRepo ===")
session_repo = DynamoSessionRepo()
sessions = session_repo.list_by_user(user_id, limit=10)
print(f"Sessions from repo: {len(sessions)}")
for s in sessions[:3]:
    print(f"  - {s.session_id}: {s.status}")

# Test use case
print("\n=== Testing ListSpeakingSessionsUseCase ===")
scoring_repo = DynamoScoringRepo()
use_case = ListSpeakingSessionsUseCase(session_repo, scoring_repo)
result = use_case.execute(user_id, limit=10)

if result.is_success:
    print(f"Use case returned {len(result.value.sessions)} sessions")
    for s in result.value.sessions[:3]:
        print(f"  - {s.session_id}: {s.status}")
else:
    print(f"Use case failed: {result.error}")
