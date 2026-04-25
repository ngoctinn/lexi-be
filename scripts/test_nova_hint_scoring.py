#!/usr/bin/env python3
"""
Test script to verify Nova Micro format for hint generation and scoring.
Validates the fixes in websocket_handler.py and bedrock_scorer_adapter.py
"""

import json
import boto3
from botocore.config import Config

# Configure retry
retry_config = Config(
    retries={
        "max_attempts": 3,
        "mode": "adaptive",
    }
)

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1", config=retry_config)

def test_hint_generation():
    """Test hint generation with Nova Micro format."""
    print("\n" + "="*60)
    print("TEST 1: Hint Generation (Nova Micro)")
    print("="*60)
    
    hint_prompt = (
        "The learner is stuck in an English conversation. "
        "Last AI message: 'Hello! How can I help you today?'. "
        "Current goal: order_food. Learner level: B1. "
        "Give a 1-sentence hint starting with 'You could say:' using simple English appropriate for B1."
    )
    
    # Nova format (per AWS docs)
    body = json.dumps({
        "system": [{"text": "You are a helpful English tutor providing hints to learners."}],
        "messages": [
            {
                "role": "user",
                "content": [{"text": hint_prompt}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 60,
            "temperature": 0.5
        }
    })
    
    try:
        print(f"\n📤 Request:")
        print(f"Model: apac.amazon.nova-micro-v1:0 (inference profile)")
        print(f"Body: {json.dumps(json.loads(body), indent=2)}")
        
        response = bedrock.invoke_model(
            modelId="apac.amazon.nova-micro-v1:0",  # Use inference profile
            body=body,
        )
        
        result = json.loads(response["body"].read())
        print(f"\n📥 Response:")
        print(json.dumps(result, indent=2))
        
        # Extract hint text
        hint_text = result["output"]["message"]["content"][0]["text"]
        print(f"\n✅ Hint: {hint_text}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_scoring():
    """Test scoring with Nova Micro format."""
    print("\n" + "="*60)
    print("TEST 2: Scoring (Nova Micro)")
    print("="*60)
    
    prompt = """Analyze this English learner's speaking performance.

Level: B1
Scenario: Restaurant Ordering
Number of turns: 2

Turns spoken:
- I'd like to order a coffee, please.
- Can I have it hot?

Score the learner (0-100) on:
1. Fluency: Smoothness, natural pacing, minimal hesitation
2. Pronunciation: Clear articulation, correct stress/intonation
3. Grammar: Correct sentence structure, verb tenses, agreement
4. Vocabulary: Word choice, variety, appropriateness for level

Respond in JSON format only:
{
  "fluency_score": <0-100>,
  "pronunciation_score": <0-100>,
  "grammar_score": <0-100>,
  "vocabulary_score": <0-100>,
  "overall_score": <0-100>,
  "feedback": "<personalized feedback in Vietnamese>"
}"""
    
    # Nova format (per AWS docs)
    body = json.dumps({
        "system": [{"text": prompt}],
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Please score the above performance."}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 500,
            "temperature": 0.7
        }
    })
    
    try:
        print(f"\n📤 Request:")
        print(f"Model: apac.amazon.nova-micro-v1:0 (inference profile)")
        print(f"Body: {json.dumps(json.loads(body), indent=2)[:500]}...")
        
        response = bedrock.invoke_model(
            modelId="apac.amazon.nova-micro-v1:0",  # Use inference profile
            body=body,
        )
        
        result = json.loads(response["body"].read())
        print(f"\n📥 Response:")
        print(json.dumps(result, indent=2)[:500] + "...")
        
        # Extract scoring JSON
        content = result["output"]["message"]["content"][0]["text"]
        scoring_data = json.loads(content)
        
        print(f"\n✅ Scoring:")
        print(f"  Fluency: {scoring_data['fluency_score']}")
        print(f"  Pronunciation: {scoring_data['pronunciation_score']}")
        print(f"  Grammar: {scoring_data['grammar_score']}")
        print(f"  Vocabulary: {scoring_data['vocabulary_score']}")
        print(f"  Overall: {scoring_data['overall_score']}")
        print(f"  Feedback: {scoring_data['feedback'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("NOVA MICRO FORMAT VERIFICATION")
    print("="*60)
    print("\nTesting fixes for:")
    print("1. websocket_handler.py - use_hint() method")
    print("2. bedrock_scorer_adapter.py - score_session() method")
    
    # Run tests
    test1_pass = test_hint_generation()
    test2_pass = test_scoring()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Hint Generation: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"Scoring: {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    if test1_pass and test2_pass:
        print("\n🎉 All tests passed! Nova Micro format is correct.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
