import os
import logging
import time
from typing import Optional, Any
from dataclasses import dataclass, asdict
import json

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

# Reuse boto3 client for Lambda warm start
_dynamodb_client = None


def _get_dynamodb_client():
    global _dynamodb_client
    if _dynamodb_client is None:
        region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
        _dynamodb_client = boto3.client("dynamodb", region_name=region) if region else boto3.client("dynamodb")
    return _dynamodb_client


class CacheService:
    """
    Two-tier cache: in-memory (fast) + DynamoDB (persistent).
    
    Uses single table design with LexiApp table:
    - PK: CACHE#{cache_key}
    - SK: CACHE#{cache_key}
    - EntityType: CACHE
    - ttl: Unix timestamp for auto-deletion
    """

    def __init__(self, table_name: str = "LexiApp"):
        self._in_memory_cache: dict[str, tuple[Any, float]] = {}  # {key: (value, expiry_time)}
        self._table_name = table_name
        self._ttl_seconds = 86400  # 24 hours

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (in-memory first, then DynamoDB).
        
        Args:
            key: Cache key (e.g., "vocabulary:definition:hello")
        
        Returns:
            Cached value or None if not found or expired
        """
        # Try in-memory cache first
        if key in self._in_memory_cache:
            value, expiry_time = self._in_memory_cache[key]
            if time.time() < expiry_time:
                logger.debug(f"Cache hit (in-memory): {key}")
                return value
            else:
                # Expired, remove from cache
                del self._in_memory_cache[key]

        # Try DynamoDB fallback with single table design
        try:
            pk = f"CACHE#{key}"
            sk = f"CACHE#{key}"
            
            response = _get_dynamodb_client().get_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": pk},
                    "SK": {"S": sk}
                }
            )
            
            if "Item" in response:
                item = response["Item"]
                # Check TTL
                ttl = int(item.get("ttl", {}).get("N", 0))
                if time.time() < ttl:
                    # Parse value from JSON
                    value_json = item.get("data", {}).get("S", "{}")
                    value = json.loads(value_json)
                    logger.debug(f"Cache hit (DynamoDB): {key}")
                    # Restore to in-memory cache
                    self._in_memory_cache[key] = (value, ttl)
                    return value
                else:
                    logger.debug(f"Cache expired (DynamoDB): {key}")
            else:
                logger.debug(f"Cache miss: {key}")
        except (ClientError, BotoCoreError) as e:
            logger.warning(f"DynamoDB cache lookup failed for {key}: {e}")
        
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 86400) -> None:
        """
        Set value in cache (in-memory + DynamoDB).
        
        Args:
            key: Cache key (e.g., "vocabulary:definition:hello")
            value: Value to cache (should be JSON-serializable)
            ttl_seconds: Time-to-live in seconds (default: 24 hours)
        """
        expiry_time = time.time() + ttl_seconds
        
        # Store in in-memory cache
        self._in_memory_cache[key] = (value, expiry_time)
        logger.debug(f"Cached in memory: {key}")
        
        # Store in DynamoDB with single table design
        try:
            pk = f"CACHE#{key}"
            sk = f"CACHE#{key}"
            value_json = json.dumps(value) if not isinstance(value, str) else value
            ttl_unix = int(expiry_time)
            
            _get_dynamodb_client().put_item(
                TableName=self._table_name,
                Item={
                    "PK": {"S": pk},
                    "SK": {"S": sk},
                    "EntityType": {"S": "CACHE"},
                    "cache_key": {"S": key},
                    "data": {"S": value_json},
                    "ttl": {"N": str(ttl_unix)},
                    "created_at": {"S": str(int(time.time()))}
                }
            )
            logger.debug(f"Cached in DynamoDB: {key}")
        except (ClientError, BotoCoreError) as e:
            logger.warning(f"DynamoDB cache storage failed for {key}: {e}")
            # Continue without DynamoDB caching (graceful degradation)

    def clear(self) -> None:
        """Clear in-memory cache."""
        self._in_memory_cache.clear()
        logger.debug("In-memory cache cleared")
