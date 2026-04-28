"""
HTTP presenter for Lambda API Gateway responses.
Converts view models to HTTP responses.
"""

import json
from typing import Any, Dict, Optional
from dataclasses import asdict

from interfaces.presenters.base import BasePresenter
from shared.http_utils import dumps


class HttpPresenter(BasePresenter):
    """HTTP presenter for API Gateway Lambda responses."""

    def __init__(self, status_code: int = 200):
        self.status_code = status_code

    def _format_response(self, status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
        """Format HTTP response with headers."""
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": dumps(body),
        }

    def present_error(
        self, error_msg: str, code: Optional[str] = None, status_code: int = 400
    ) -> Dict[str, Any]:
        """Format error response to HTTP."""
        return self._format_response(status_code, {
            "error": error_msg,
            "code": code or "ERROR"
        })

    def present_success(
        self, data: Any, message: str = "Success", status_code: int = 200
    ) -> Dict[str, Any]:
        """Format success response to HTTP."""
        if hasattr(data, '__dataclass_fields__'):
            # Use fields() approach as recommended by Python docs for safety
            from dataclasses import fields
            try:
                data_dict = {field.name: getattr(data, field.name) for field in fields(data)}
            except Exception:
                # Fallback to manual field extraction
                data_dict = {}
                for field_name in data.__dataclass_fields__:
                    data_dict[field_name] = getattr(data, field_name)
        elif hasattr(data, 'model_dump'):  # Pydantic v2
            data_dict = data.model_dump()
        elif hasattr(data, 'dict'):  # Pydantic v1
            data_dict = data.dict()
        elif isinstance(data, dict):
            data_dict = data
        else:
            data_dict = {"result": data}
        
        return self._format_response(status_code, {
            "success": True,
            "message": message,
            "data": data_dict,
        })

    def present_created(self, data: Any, message: str = "Created") -> Dict[str, Any]:
        """Format 201 Created response."""
        return self.present_success(data, message, status_code=201)

    def present_not_found(self, message: str = "Not found") -> Dict[str, Any]:
        """Format 404 Not Found response."""
        return self._format_response(404, {
            "error": message,
            "code": "NOT_FOUND"
        })

    def present_unauthorized(self, message: str = "Unauthorized") -> Dict[str, Any]:
        """Format 401 Unauthorized response."""
        return self._format_response(401, {
            "error": message,
            "code": "UNAUTHORIZED"
        })

    def present_bad_request(self, message: str = "Bad request") -> Dict[str, Any]:
        """Format 400 Bad Request response."""
        return self._format_response(400, {
            "error": message,
            "code": "BAD_REQUEST"
        })
