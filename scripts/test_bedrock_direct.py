#!/usr/bin/env python3
"""
Direct Bedrock Test - Test invoke_model_with_response_stream
"""

import json
import boto3
from botocore.config import Config

# Configure retry with exponential backoff
retry_config = Config(
    retries={
        "max_attempts": 3,
        "mode": "adaptive",
    }
)

bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1", config=retry_config)

def test_bedrock_streaming():
    """Test Bedrock streaming API"""
    print("Testing Bedrock invoke_model_with_response_stream...")
    
    model_id = "amazon.nova-micro-v1:0"
    
    request_body = json.dumps({
        "system": [{"text": "You are a helpful assistant."}],
        "messages": [
            {
                "role": "user",
                "content": [{"text": "Hello, how are you?"}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 100,
            "temperature": 0.7
        }
    })
    
    try:
        response = bedrock_client.invoke_model_with_response_stream(
            modelId=model_id,
            body=request_body,
        )
        
        print(f"✅ Successfully called Bedrock streaming API")
        print(f"Response type: {type(response)}")
        
        # Process event stream
        event_stream = response["body"]
        full_response = ""
        
        for event in event_stream:
            print(f"Event: {event}")
            if "chunk" in event:
                chunk_bytes = event["chunk"]["bytes"]
                chunk_json = json.loads(chunk_bytes.decode("utf-8"))
                print(f"Chunk JSON: {chunk_json}")
                
                if "delta" in chunk_json and "text" in chunk_json["delta"]:
                    text = chunk_json["delta"]["text"]
                    full_response += text
                    print(f"Token: {text}", end="", flush=True)
        
        print(f"\n\n✅ Full response:\n{full_response}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_bedrock_streaming()
    exit(0 if success else 1)
