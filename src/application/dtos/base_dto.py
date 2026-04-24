from decimal import Decimal
from pydantic import BaseModel, field_serializer

class BaseDTO(BaseModel):
    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "ignore"  # Allow extra fields (Phase 5: metrics fields)
    }
    
    @field_serializer('*', mode='wrap')
    def serialize_decimal(self, value, handler, info):
        """Convert Decimal to float for JSON serialization (DynamoDB compatibility)."""
        if isinstance(value, Decimal):
            return float(value)
        return handler(value)