"""
HTTP presenter for Lambda API Gateway responses.
Converts view models to HTTP responses.
"""

import json
from typing import Any, Dict, Optional
from dataclasses import asdict

from interfaces.presenters.base import BasePresenter
from interfaces.view_models.base import ErrorViewModel, OperationResult
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
    ) -> ErrorViewModel:
        """Format error to ErrorViewModel."""
        return ErrorViewModel(message=error_msg, code=code or "ERROR")

    def present_success(
        self, data: Any, message: str = "Success", status_code: int = 200
    ) -> Dict[str, Any]:
        """Format success response to HTTP."""
        if hasattr(data, '__dataclass_fields__'):
            data_dict = asdict(data)
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
        error_vm = self.present_error(message, code="NOT_FOUND", status_code=404)
        return self._format_response(404, asdict(error_vm))

    def present_unauthorized(self, message: str = "Unauthorized") -> Dict[str, Any]:
        """Format 401 Unauthorized response."""
        error_vm = self.present_error(message, code="UNAUTHORIZED", status_code=401)
        return self._format_response(401, asdict(error_vm))

    def present_bad_request(self, message: str = "Bad request") -> Dict[str, Any]:
        """Format 400 Bad Request response."""
        error_vm = self.present_error(message, code="BAD_REQUEST", status_code=400)
        return self._format_response(400, asdict(error_vm))

    def format_operation_result(self, result: OperationResult[Any]) -> Dict[str, Any]:
        """Convert OperationResult to HTTP response."""
        if result.is_success:
            return self.present_success(result.success)
        else:
            error = result.error
            return self._format_response(400, asdict(error))
