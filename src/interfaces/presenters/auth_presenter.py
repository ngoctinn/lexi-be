import json


class AuthPresenter:
    @staticmethod
    def _response(status_code: int, body: dict) -> dict:
        return {
            "statusCode": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body),
        }

    @staticmethod
    def success(message: str, status_code: int = 200) -> dict:
        return AuthPresenter._response(status_code, {"message": message})

    @staticmethod
    def tokens(data: dict) -> dict:
        return AuthPresenter._response(200, data)

    @staticmethod
    def error(message: str, status_code: int = 400) -> dict:
        return AuthPresenter._response(status_code, {"error": message})
