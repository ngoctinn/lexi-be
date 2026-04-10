# interface_adapters/presenters/base_presenter.py
import json

class BasePresenter:
    @staticmethod
    def _build_response(status_code: int, body: dict):
        """Hàm dùng chung để đóng gói cấu trúc Lambda Response"""
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*" # Quan trọng để tránh lỗi CORS
            },
            "body": json.dumps(body)
        }

    @staticmethod
    def success(data, status_code=200):
        """Dùng cho các trường hợp trả về dữ liệu thành công"""
        return BasePresenter._build_response(status_code, data)

    @staticmethod
    def error(message: str, status_code=400, details=None):
        """Dùng cho các trường hợp trả về lỗi"""
        error_body = {"error": message}
        if details:
            error_body["details"] = details
        return BasePresenter._build_response(status_code, error_body)