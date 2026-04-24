from decimal import Decimal
from pydantic import BaseModel, ConfigDict, model_serializer

class BaseDTO(BaseModel):
    # Pydantic v2 configuration
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore",  # Allow extra fields (Phase 5: metrics fields)
    )
    
    @model_serializer(mode='wrap')
    def serialize_model(self, serializer, info):
        """Serialize model to JSON, converting Decimal to float."""
        data = serializer(self)
        
        # Only convert Decimals to float when serializing to JSON
        if info.mode == 'json':
            def convert_decimals(obj):
                """Recursively convert Decimal to float."""
                if isinstance(obj, dict):
                    return {k: convert_decimals(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_decimals(item) for item in obj]
                elif isinstance(obj, Decimal):
                    return float(obj)
                return obj
            
            return convert_decimals(data)
        
        return data