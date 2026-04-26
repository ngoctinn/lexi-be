#!/usr/bin/env python3
"""
Test StreamingResponse class with Amazon Nova
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import boto3
from botocore.config import Config
from domain.services.streaming_response import StreamingResponse

# Configure retry with exponential backoff
retry_config = Config(
    retries={
        "max_attempts": 3,
        "mode": "adaptive",
    }
)

bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1", config=retry_config)

def test_streaming_response_class():
    """Test StreamingResponse class with Nova"""
    print("Testing StreamingResponse class with Amazon Nova...")
    
    # Create StreamingResponse instance
    streaming = StreamingResponse(timeout_seconds=10.0, bedrock_client=bedrock_client)
    
    try:
        # Test invoke_with_streaming method
        response = streaming.invoke_with_streaming(
            model_id="amazon.nova-micro-v1:0",
            system_prompt="You are a helpful assistant.",
            user_message="Hello, how are you?",
            max_tokens=100,
            temperature=0.7,
        )
        
        print(f"✅ StreamingResponse.invoke_with_streaming() successful")
        print(f"Response text: '{response['text']}'")
        print(f"TTFT: {response['ttft_ms']}ms")
        print(f"Latency: {response['latency_ms']}ms")
        print(f"Input tokens: {response['input_tokens']}")
        print(f"Output tokens: {response['output_tokens']}")
        print(f"Error: {response['error_message']}")
        print(f"Timeout: {response['is_timeout']}")
        
        # Verify we got actual text
        if response['text'] and len(response['text'].strip()) > 0:
            print("✅ Text extraction working correctly")
            return True
        else:
            print("❌ No text extracted from streaming response")
            return False
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_streaming_response_class()
    exit(0 if success else 1)