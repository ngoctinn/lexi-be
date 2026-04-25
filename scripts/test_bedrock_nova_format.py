#!/usr/bin/env python3
"""
Test Bedrock with exact Nova format used in speaking_pipeline_services.py
"""

import json
import boto3
from botocore.config import Config

# Configure retry with exponential backoff (same as production)
retry_config = Config(
    retries={
        "max_attempts": 3,
        "mode": "adaptive",
    }
)

bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1", config=retry_config)

def test_nova_format():
    """Test with exact Nova format from speaking_pipeline_services.py"""
    print("Testing Bedrock with Nova format (exact production format)...\n")
    
    model_id = "amazon.nova-micro-v1:0"
    
    # Exact format from speaking_pipeline_services.py
    request_body = json.dumps({
        "system": [
            {
                "text": "You are a helpful English conversation partner. Help the learner practice English."
            },
            {
                "text": "Current scenario: Business Meeting"
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Hello, how are you?"}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 150,
            "temperature": 0.7,
        }
    })
    
    try:
        response = bedrock_client.invoke_model_with_response_stream(
            modelId=model_id,
            body=request_body,
        )
        
        print(f"✅ Successfully called Bedrock streaming API")
        
        # Process event stream (exact format from speaking_pipeline_services.py)
        event_stream = response["body"]
        full_response = ""
        
        for event in event_stream:
            if "chunk" in event:
                chunk_bytes = event["chunk"]["bytes"]
                chunk_json = json.loads(chunk_bytes.decode("utf-8"))
                
                # Extract text from chunk (Nova format)
                if "contentBlockDelta" in chunk_json:
                    delta = chunk_json["contentBlockDelta"].get("delta", {})
                    if "text" in delta:
                        text = delta["text"]
                        full_response += text
                        print(text, end="", flush=True)
        
        print(f"\n\n✅ Full response received ({len(full_response)} chars)")
        print(f"✅ Bedrock is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_nova_format()
    exit(0 if success else 1)
