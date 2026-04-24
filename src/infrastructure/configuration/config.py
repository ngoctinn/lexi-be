"""
Infrastructure configuration for Lexi application.
Manages environment variables and application settings.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional

# Load environment variables only in development
# In Lambda, environment variables are set by AWS and .env files are not available
if os.getenv("ENVIRONMENT", "development") == "development":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # dotenv not installed in development environment
        pass


class Environment(Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Config:
    """Central configuration management."""

    # Environment
    ENVIRONMENT = Environment(os.getenv("ENVIRONMENT", "development"))
    
    # AWS
    AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
    LEXI_TABLE_NAME = os.getenv("LEXI_TABLE_NAME", "lexi-table")
    
    # Services
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
    TRANSLATE_SERVICE_REGION = os.getenv("TRANSLATE_SERVICE_REGION", "ap-southeast-1")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = Path(os.getenv("LOG_DIR", "/tmp/logs"))
    
    # Feature flags
    ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() == "true"
    ENABLE_SCORING = os.getenv("ENABLE_SCORING", "true").lower() == "true"
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production."""
        return cls.ENVIRONMENT == Environment.PRODUCTION
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development."""
        return cls.ENVIRONMENT == Environment.DEVELOPMENT
    
    @classmethod
    def get_log_dir(cls) -> Path:
        """Get log directory, creating if needed."""
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        return cls.LOG_DIR
