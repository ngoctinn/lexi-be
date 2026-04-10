import json

from pydantic import ValidationError

from application.dtos.flashcard.create.create_flashcard_command import CreateFlashCardCommand
from application.dtos.flashcard.delete.delete_flashcard_command import DeleteFlashCardCommand
from application.usecases.flashcard.create_flashcard_uc import CreateFlashCardUC
from interfaces.presenters.base_presenter import BasePresenter

class FlashCardController:
    def __init__(self, create_flashcard_usecase: CreateFlashCardUC, presenter: BasePresenter):
        self._create_flashcard_usecase = create_flashcard_usecase
        self._presenter = presenter

    def create(self, event):
        try:
            # 1. Parsing & Validation với Pydantic
            body_str = event.get('body', '{}')
            body_data = json.loads(body_str)
            
            # Trích xuất user_id từ Authorizer
            user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
            body_data['user_id'] = user_id

            # Ánh xạ JSON vào DTO (Command)
            command = CreateFlashCardCommand(**body_data)

            # 2. Gọi Use Case
            # Use Case trả về một Domain Entity hoặc một Response DTO
            result = self.create_flashcard_usecase.execute(command)

            # 3. Trả về Response thành công (201 Created)
            return self._presenter.success(result, 201)

        except ValidationError as e:
            # Lỗi dữ liệu đầu vào không hợp lệ
            return self._presenter.error("Dữ liệu đầu vào không hợp lệ", 400, e.errors())
            
        except Exception as e:
            # Lỗi hệ thống không mong muốn
            return self._presenter.error("Đã xảy ra lỗi hệ thống", 500, str(e)) 

    def delete(self, event):
        try:
            # 1. Trích xuất flashcard_id từ pathParameters (Ví dụ: /flashcards/{id})
            path_params = event.get('pathParameters', {})
            flashcard_id = path_params.get('id')
            
            if not flashcard_id:
                return self._presenter.error("Thiếu ID của Flashcard", 400)

            command = DeleteFlashCardCommand(flashcard_id=flashcard_id)

            # 2. Gọi Use Case để thực hiện xóa
            self.delete_flashcard_usecase.execute()

            # 3. Trả về response thành công (204 No Content là chuẩn nhất cho xóa)
            return self._presenter.success(None, 204)

        except Exception as e:
            return self._presenter.error("Đã xảy ra lỗi hệ thống", 500, str(e)) 
