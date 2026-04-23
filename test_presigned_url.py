#!/usr/bin/env python3
"""Test script to generate and test S3 presigned URL upload"""

import boto3
import requests
import os

# Configuration
BUCKET_NAME = "lexi-be-speakingaudiobucket-0jxmvjgjn0xv"
REGION = "ap-southeast-1"
TEST_KEY = "test-uploads/test-audio.webm"
TEST_FILE = "/tmp/test-audio.webm"

# Create S3 client
s3_client = boto3.client("s3", region_name=REGION)

# Generate presigned URL WITHOUT ContentType
print("Generating presigned URL WITHOUT ContentType...")
presigned_url = s3_client.generate_presigned_url(
    ClientMethod="put_object",
    Params={
        "Bucket": BUCKET_NAME,
        "Key": TEST_KEY,
    },
    ExpiresIn=900,
    HttpMethod="PUT",
)

print(f"Presigned URL: {presigned_url[:200]}...")
print(f"URL length: {len(presigned_url)}")

# Test upload with curl
print("\nTesting upload with curl...")
os.system(f'curl -X PUT -T "{TEST_FILE}" -H "Content-Type: audio/webm" "{presigned_url}" -v')

print("\n\nDone!")
