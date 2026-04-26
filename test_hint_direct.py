#!/usr/bin/env python3
"""Test hint generation directly with structured_hint_generator."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import boto3
from botocore.config import Config
from domain.services.structured_hint_generator import StructuredHintGenerator
from domain.entities.session import Session
from domain.value_objects.enums import ProficiencyLevel
from dataclasses import dataclass

# Mock Turn class
@dataclass
class MockTurn:
    content: str
    speaker: str
    turn_index: int

# Configure retry
retry_config = Config(
    retries={
        "max_attempts": 3,
        "mode": "adaptive",
    }
)

bedrock = boto3.client("bedrock-runtime", region_name="ap-southeast-1", config=retry_config)

def test_hint_generation():
    """Test hint generation with real session data."""
    print("\n" + "="*60)
    print("TEST: Structured Hint Generation")
    print("="*60)
    
    # Create mock session
    session = Session(
        session_id="test-session-123",
        user_id="test-user",
        scenario_id="restaurant-ordering",
        scenario_title="Restaurant Ordering",
        level=ProficiencyLevel.B1,
        selected_goal="order_food",
        learner_role_id="customer",
        ai_role_id="waiter",
    )
    
    # Create mock turns
    last_ai_turn = MockTurn(
        content="Hello! What would you like to order today?",
        speaker="AI",
        turn_index=1
    )
    
    turn_history = [last_ai_turn]
    
    try:
        print(f"\n📤 Generating hint for:")
        print(f"  Session: {session.session_id}")
        print(f"  Level: {session.level.value}")
        print(f"  Last AI message: {last_ai_turn.content}")
        
        # Generate hint
        hint_generator = StructuredHintGenerator(bedrock)
        hint = hint_generator.generate(
            session=session,
            last_ai_turn=last_ai_turn,
            turn_history=turn_history,
        )
        
        print(f"\n✅ Hint generated successfully!")
        print(f"  Type: {hint.type}")
        print(f"  Level: {hint.level}")
        print(f"\n📝 Vietnamese:")
        print(hint.markdown_vi)
        print(f"\n📝 English:")
        print(hint.markdown_en)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_hint_generation()
    exit(0 if success else 1)
