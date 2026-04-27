"""
Generate presigned WebSocket URLs for Amazon Transcribe streaming.

This service generates SigV4 signed WebSocket URLs that browser clients can use
to connect directly to Amazon Transcribe for real-time streaming transcription.

Reference: https://docs.aws.amazon.com/transcribe/latest/dg/streaming-setting-up.html#streaming-websocket

Architecture:
    Browser → Presigned WebSocket URL → Transcribe
            (direct connection, no Lambda hop)

Benefits:
    - No deprecated SDK dependency
    - Lower latency (direct browser → Transcribe)
    - No Lambda timeout issues
    - AWS officially recommended for browser clients
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone
from urllib.parse import quote, urlencode

import boto3
from botocore.credentials import Credentials

logger = logging.getLogger(__name__)

# AWS Transcribe WebSocket endpoints by region
# Reference: https://docs.aws.amazon.com/general/latest/gr/transcribe.html
TRANSCRIBE_WEBSOCKET_ENDPOINTS = {
    "us-east-1": "wss://transcribestreaming.us-east-1.amazonaws.com:8443",
    "us-east-2": "wss://transcribestreaming.us-east-2.amazonaws.com:8443",
    "us-west-2": "wss://transcribestreaming.us-west-2.amazonaws.com:8443",
    "ap-southeast-1": "wss://transcribestreaming.ap-southeast-1.amazonaws.com:8443",
    "ap-southeast-2": "wss://transcribestreaming.ap-southeast-2.amazonaws.com:8443",
    "ap-northeast-1": "wss://transcribestreaming.ap-northeast-1.amazonaws.com:8443",
    "ap-northeast-2": "wss://transcribestreaming.ap-northeast-2.amazonaws.com:8443",
    "eu-west-1": "wss://transcribestreaming.eu-west-1.amazonaws.com:8443",
    "eu-west-2": "wss://transcribestreaming.eu-west-2.amazonaws.com:8443",
    "eu-central-1": "wss://transcribestreaming.eu-central-1.amazonaws.com:8443",
}

# Default values
DEFAULT_LANGUAGE_CODE = "en-US"
DEFAULT_MEDIA_ENCODING = "pcm"  # AWS Transcribe recommended encoding
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_EXPIRES_IN = 300  # 5 minutes (AWS max)


class TranscribePresignedUrlGenerator:
    """
    Generate presigned WebSocket URLs for Amazon Transcribe streaming.
    
    Usage:
        generator = TranscribePresignedUrlGenerator()
        url = generator.generate(
            language_code="en-US",
            media_encoding="opus",
            sample_rate=16000,
        )
    """
    
    def __init__(self, region: str | None = None):
        """
        Initialize the generator.
        
        Args:
            region: AWS region. If not provided, uses AWS_REGION env var or defaults to ap-southeast-1.
        """
        self._region = region or os.environ.get("AWS_REGION", "ap-southeast-1")
        self._endpoint = TRANSCRIBE_WEBSOCKET_ENDPOINTS.get(
            self._region,
            f"wss://transcribestreaming.{self._region}.amazonaws.com:8443"
        )
        self._host = self._endpoint.replace("wss://", "")
        
        # Get credentials from boto3 session
        session = boto3.Session()
        credentials = session.get_credentials()
        self._access_key = credentials.access_key
        self._secret_key = credentials.secret_key
        self._session_token = credentials.token  # For temporary credentials (Lambda)
    
    def generate(
        self,
        language_code: str = DEFAULT_LANGUAGE_CODE,
        media_encoding: str = DEFAULT_MEDIA_ENCODING,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        expires_in: int = DEFAULT_EXPIRES_IN,
    ) -> dict:
        """
        Generate a presigned WebSocket URL for Transcribe streaming.
        
        Args:
            language_code: Language code (e.g., "en-US", "vi-VN")
            media_encoding: Audio encoding - supported values:
                - "pcm" (recommended) - Uncompressed PCM, best compatibility
                - "ogg-opus" - Opus in Ogg container
                - "flac" - FLAC lossless
            sample_rate: Audio sample rate in Hz (16000 recommended)
            expires_in: URL expiry time in seconds (max 300)
        
        Returns:
            Dict with keys:
                - url: Presigned WebSocket URL
                - expires_in: Expiry time in seconds
                - language_code: Language code
                - media_encoding: Audio encoding
                - sample_rate: Sample rate
        
        Reference:
            https://docs.aws.amazon.com/transcribe/latest/dg/streaming-setting-up.html#streaming-websocket
        """
        # Validate expires_in (AWS max is 300 seconds)
        if expires_in > 300:
            logger.warning(f"expires_in={expires_in} exceeds AWS max of 300, using 300")
            expires_in = 300
        
        # Get current time
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        
        # Step 1: Create canonical request
        # Reference: https://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
        
        method = "GET"
        canonical_uri = "/stream-transcription-websocket"
        
        # Build query string parameters (must be sorted)
        # Reference: AWS docs say parameters must be sorted by name
        credential_scope = f"{date_stamp}/{self._region}/transcribe/aws4_request"
        
        query_params = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": f"{self._access_key}/{credential_scope}",
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(expires_in),
            "X-Amz-SignedHeaders": "host",
            "language-code": language_code,
            "media-encoding": media_encoding,
            "sample-rate": str(sample_rate),
        }
        
        # Add session token if using temporary credentials (Lambda)
        if self._session_token:
            query_params["X-Amz-Security-Token"] = self._session_token
        
        # Sort and encode query string
        canonical_querystring = self._build_canonical_querystring(query_params)
        
        # Canonical headers (must end with \n)
        canonical_headers = f"host:{self._host}\n"
        signed_headers = "host"
        
        # Payload hash (empty for GET requests)
        payload_hash = hashlib.sha256(b"").hexdigest()
        
        # Build canonical request
        canonical_request = "\n".join([
            method,
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            payload_hash,
        ])
        
        # Step 2: Create string to sign
        # Reference: https://docs.aws.amazon.com/general/latest/gr/sigv4-create-string-to-sign.html
        
        string_to_sign = "\n".join([
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ])
        
        # Step 3: Calculate signature
        # Reference: https://docs.aws.amazon.com/general/latest/gr/sigv4-calculate-signature.html
        
        signing_key = self._get_signature_key(date_stamp)
        signature = hmac.new(
            signing_key,
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        
        # Step 4: Build final URL
        # Reference: https://docs.aws.amazon.com/general/latest/gr/sigv4-add-signature-to-request.html
        
        final_querystring = f"{canonical_querystring}&X-Amz-Signature={signature}"
        request_url = f"{self._endpoint}{canonical_uri}?{final_querystring}"
        
        logger.info(
            "Generated Transcribe presigned URL",
            extra={
                "region": self._region,
                "language_code": language_code,
                "media_encoding": media_encoding,
                "sample_rate": sample_rate,
                "expires_in": expires_in,
            },
        )
        
        return {
            "url": request_url,
            "expires_in": expires_in,
            "language_code": language_code,
            "media_encoding": media_encoding,
            "sample_rate": sample_rate,
        }
    
    def _build_canonical_querystring(self, params: dict) -> str:
        """
        Build canonical query string from parameters.
        
        Rules:
        - Sort by parameter name
        - URI encode parameter names and values
        - Use %20 for spaces (not +)
        
        Reference: https://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
        """
        # Sort by parameter name
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # Encode and join
        encoded_params = []
        for key, value in sorted_params:
            # URI encode key and value
            # AWS requires specific encoding: A-Z, a-z, 0-9, -, _, ., ~ are not encoded
            encoded_key = self._uri_encode(key)
            encoded_value = self._uri_encode(value)
            encoded_params.append(f"{encoded_key}={encoded_value}")
        
        return "&".join(encoded_params)
    
    def _uri_encode(self, value: str) -> str:
        """
        URI encode a string according to AWS SigV4 rules.
        
        Do not encode: A-Z, a-z, 0-9, -, _, ., ~
        Encode everything else with %XX
        
        Reference: https://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html
        """
        # Use quote with safe characters
        # safe="" means encode everything except explicitly listed
        return quote(str(value), safe="-_.~")
    
    def _get_signature_key(self, date_stamp: str) -> bytes:
        """
        Derive signing key from secret key.
        
        The signing key is derived from the secret key and is specific to:
        - Date
        - Region
        - Service (transcribe)
        
        Reference: https://docs.aws.amazon.com/general/latest/gr/sigv4-calculate-signature.html
        """
        k_date = self._hmac_sha256(("AWS4" + self._secret_key).encode("utf-8"), date_stamp)
        k_region = self._hmac_sha256(k_date, self._region)
        k_service = self._hmac_sha256(k_region, "transcribe")
        k_signing = self._hmac_sha256(k_service, "aws4_request")
        return k_signing
    
    @staticmethod
    def _hmac_sha256(key: bytes, msg: str) -> bytes:
        """Compute HMAC-SHA256."""
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
