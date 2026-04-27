import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """
    Custom JSON encoder xử lý kiểu Decimal từ DynamoDB resource interface.
    Theo boto3 docs: DynamoDB trả về số dưới dạng decimal.Decimal,
    cần convert sang int hoặc float trước khi json.dumps.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Giữ nguyên int nếu không có phần thập phân
            return int(obj) if obj % 1 == 0 else float(obj)
        # Handle Pydantic v2 models
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        # Handle Pydantic v1 models
        if hasattr(obj, 'dict'):
            return obj.dict()
        # Handle dataclasses
        if hasattr(obj, '__dataclass_fields__'):
            from dataclasses import asdict
            return asdict(obj)
        return super().default(obj)


def dumps(data, ensure_ascii: bool = True) -> str:
    """json.dumps với DecimalEncoder — dùng thay thế json.dumps trong toàn bộ handlers."""
    return json.dumps(data, cls=DecimalEncoder, ensure_ascii=ensure_ascii)


def parse_body(event: dict) -> dict:
    try:
        return json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON body")


def require_fields(body: dict, *fields: str) -> None:
    # Consider a field missing only if it's not present in the body or is None.
    # This avoids treating falsy-but-valid values like 0 or False as missing.
    missing = [f for f in fields if f not in body or body.get(f) is None]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
