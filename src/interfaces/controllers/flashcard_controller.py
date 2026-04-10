import json

from pydantic import ValidationError

from application.dtos.flashcard.create.create_flashcard_command import CreateFlashCardCommand

class FlashCardController:
    def __init__(self, create_flashcard_usecase):
        self.create_flashcard_usecase = create_flashcard_usecase

    def create(self, event):
        try:
            # 1. Parsing & Validation với Pydantic
            # AWS Lambda event['body'] thường là một chuỗi JSON
            body_str = event.get('body', '{}')
            body_data = json.loads(body_str)
            
            # Trích xuất user_id từ Authorizer (nếu bạn dùng Cognito/JWT)
            user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
            
            # Ánh xạ JSON vào DTO (Command)
            # Nếu dữ liệu thiếu hoặc sai kiểu, Pydantic sẽ ném lỗi ValidationError
            command = CreateFlashCardCommand(**body_data)

            # 2. Gọi Use Case
            # Use Case trả về một Domain Entity hoặc một Response DTO
            result = self.create_flashcard_usecase.execute(command)

            # 3. Trả về Response thành công (201 Created)
            return {
                "statusCode": 201,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(result.model_dump()) # Pydantic v2 dùng model_dump
            }

        except ValidationError as e:
            # Lỗi dữ liệu đầu vào không hợp lệ
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Validation Error", "details": e.errors()})
            }
        except Exception as e:
            # Lỗi hệ thống không mong muốn
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Internal Server Error"})
            }

    def delete(self, event):
        try:
            # 1. Trích xuất flashcard_id từ pathParameters (Ví dụ: /flashcards/{id})
            path_params = event.get('pathParameters', {})
            flashcard_id = path_params.get('id')
            
            if not flashcard_id:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"message": "Thiếu ID của Flashcard"})
                }

            # 2. Gọi Use Case để thực hiện xóa
            self.delete_flashcard_usecase.execute(flashcard_id=flashcard_id)

            # 3. Trả về response thành công (204 No Content là chuẩn nhất cho xóa)
            return {
                "statusCode": 204,
                "body": "" # Xóa thành công thường không trả về body
            }

        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Không thể xóa Flashcard này"})
            }