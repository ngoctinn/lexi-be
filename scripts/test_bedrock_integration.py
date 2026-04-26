#!/usr/bin/env python3
"""
Integration test: Verify Bedrock is called with correct format
"""

import sys
import json
sys.path.insert(0, 'src')

from infrastructure.services.speaking_pipeline_services import BedrockConversationGenerationService
from domain.entities.session import Session
from domain.entities.turn import Turn
from application.service_ports.speaking_services import SpeakingAnalysis
from domain.value_objects.enums import ProficiencyLevel, Speaker, Gender

def test_bedrock_call():
    """Test that Bedrock is called with correct Nova format"""
    print("Testing Bedrock integration...")
    print("")
    
    # Create mock session
    session = Session(
        session_id="test-session",
        user_id="test-user",
        scenario_id="scenario-1",
        scenario_title="Business Meeting",
        learner_role_id="learner",
        ai_role_id="ai",
        level=ProficiencyLevel.A1,
        selected_goal="greeting",
        ai_gender=Gender.FEMALE,
        created_at="2026-04-25T00:00:00Z",
        updated_at="2026-04-25T00:00:00Z"
    )
    
    # Create mock turn
    user_turn = Turn(
        turn_id="turn-1",
        session_id="test-session",
        speaker=Speaker.USER,
        content="Hello, how are you?",
        turn_index=0,
        created_at="2026-04-25T00:00:00Z"
    )
    
    # Create mock analysis
    analysis = SpeakingAnalysis(
        key_phrases=["hello"],
        word_count=4,
        unique_word_count=4,
        sentence_count=1,
        syntax_notes=[],
        dominant_language="en"
    )
    
    # Create service
    service = BedrockConversationGenerationService()
    
    try:
        # Call Bedrock
        print("Calling Bedrock with Nova format...")
        response = service.generate_reply(
            session=session,
            user_turn=user_turn,
            analysis=analysis,
            turn_history=[]
        )
        
        print(f"✅ Response received!")
        print(f"Response: {response[:200]}...")
        
        # Check if it's real response or fallback
        if response == "I see. Could you tell me more about that?":
            print("❌ Got fallback response (Bedrock not called)")
            return False
        else:
            print("✅ Got REAL Bedrock response!")
            return True
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_bedrock_call()
    exit(0 if success else 1)
