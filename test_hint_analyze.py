"""Test script to reproduce hint and analyze_turn errors."""

import boto3
import os
from unittest.mock import Mock

# Set up environment
os.environ["AWS_REGION"] = "ap-southeast-1"

# Import services
from src.domain.services.structured_hint_generator import StructuredHintGenerator
from src.domain.services.conversation_analyzer import ConversationAnalyzer

# Create mock bedrock client
bedrock_client = boto3.client("bedrock-runtime", region_name="ap-southeast-1")

# Test 1: Hint Generator
print("=" * 50)
print("TEST 1: Hint Generator")
print("=" * 50)

try:
    # Create mock session
    mock_session = Mock()
    mock_session.session_id = "test-session-123"
    mock_session.scenario_title = "Coffee Shop"
    mock_session.scenario_id = "coffee-shop"
    mock_session.learner_role_id = "customer"
    mock_session.ai_role_id = "barista"
    mock_session.level = Mock(value="A1")
    mock_session.selected_goal = "ordering food"
    mock_session.ai_character = "Sarah"
    
    # Create mock last AI turn
    mock_ai_turn = Mock()
    mock_ai_turn.content = "What would you like to order?"
    
    # Create hint generator
    hint_gen = StructuredHintGenerator(bedrock_client)
    
    # Generate hint
    print("Generating hint...")
    hint = hint_gen.generate(
        session=mock_session,
        last_ai_turn=mock_ai_turn,
        turn_history=[],
    )
    
    print(f"✅ Hint generated successfully!")
    print(f"Type: {hint.type}")
    print(f"Level: {hint.level}")
    print(f"Vietnamese: {hint.markdown_vi[:100]}...")
    print(f"English: {hint.markdown_en[:100]}...")
    
except Exception as e:
    print(f"❌ Hint generation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Conversation Analyzer
print("\n" + "=" * 50)
print("TEST 2: Conversation Analyzer")
print("=" * 50)

try:
    # Create analyzer
    analyzer = ConversationAnalyzer(bedrock_client=bedrock_client)
    
    # Analyze turn
    print("Analyzing turn...")
    analysis = analyzer.analyze_turn(
        learner_message="I go to school yesterday",
        ai_response="That's interesting! What did you do at school?",
        level="A1",
        scenario_context="Daily routine conversation",
    )
    
    print(f"✅ Analysis completed successfully!")
    print(f"Vietnamese: {analysis.markdown_vi[:100]}...")
    print(f"English: {analysis.markdown_en[:100]}...")
    
except Exception as e:
    print(f"❌ Analysis failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("TESTS COMPLETED")
print("=" * 50)
