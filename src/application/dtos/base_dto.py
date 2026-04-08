from pydantic import BaseModel

class BaseDTO(BaseModel):
    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "forbid"
    }