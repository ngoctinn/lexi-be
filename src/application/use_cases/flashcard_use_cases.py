"""Flashcard Use Cases - Consolidated from individual files."""

from typing import List, Optional
from datetime import datetime, timezone, timedelta
from ulid import ULID
from application.dtos.flashcard_dtos import CreateFlashCardCommand, CreateFlashCardResponse
from application.repositories.flash_card_repository import FlashCardRepository
from domain.entities.flashcard import FlashCard
from shared.result import Result


class CreateFlashCardUseCase:
    """
    Ca sử dụng: Tạo thẻ từ vựng (FlashCard) mới cho người dùng.
    
    Quy trình:
    1. Kiểm tra từ vựng đã tồn tại trong kho thẻ của người dùng chưa.
    2. Nếu chưa, tạo thực thể FlashCard mới với ID duy nhất (ULID).
    3. Lưu vào cơ sở dữ liệu thông qua Repository.
    4. Trả về kết quả thành công kèm thông tin thẻ.
    """
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(self, command: CreateFlashCardCommand) -> Result[CreateFlashCardResponse, str]:
        """
        Thực thi trình tự tạo thẻ ghi nhớ.
        """
        # 1. Kiểm tra trùng lặp (Idempotency check)
        existing_card = self._repo.get_by_user_and_word(command.user_id, command.word)
        if existing_card:
            return Result.failure(f"Từ vựng '{command.word}' đã có trong kho thẻ của bạn.")

        # 2. Tạo thực thể Domain mới
        try:
            flashcard = FlashCard(
                flashcard_id=str(ULID()),
                user_id=command.user_id,
                word=command.word,
                translation_vi=command.translation_vi or "",
                phonetic=command.phonetic or "",
                audio_url=command.audio_url or "",
                example_sentence=command.example_sentence or "",
                source_session_id=command.source_session_id,
                source_turn_index=command.source_turn_index,
            )
        except ValueError as e:
            return Result.failure(str(e))

        # 3. Lưu trữ
        try:
            self._repo.save(flashcard)
        except Exception as e:
            return Result.failure(f"Không thể lưu thẻ từ vựng: {str(e)}")

        # 4. Trả về kết quả
        response = CreateFlashCardResponse(
            flashcard_id=flashcard.flashcard_id,
            word=flashcard.word,
            translation_vi=flashcard.translation_vi,
            phonetic=flashcard.phonetic,
            audio_url=flashcard.audio_url,
            example_sentence=flashcard.example_sentence,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        return Result.success(response)


class GetFlashcardDetailUseCase:
    """
    Ca sử dụng: Lấy thông tin chi tiết của một thẻ từ vựng.
    
    Quy trình:
    1. Lấy thẻ từ repository theo user_id và flashcard_id
    2. Kiểm tra quyền sở hữu
    3. Trả về thẻ
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(self, user_id: str, flashcard_id: str) -> FlashCard:
        """
        Thực thi trình tự lấy chi tiết thẻ từ vựng.
        
        Raises:
            KeyError: Nếu thẻ không tồn tại
            PermissionError: Nếu thẻ không thuộc về user
        """
        # 1. Lấy thẻ từ repository
        card = self._repo.get_by_user_and_id(user_id, flashcard_id)
        if card is None:
            raise KeyError(f"Flashcard {flashcard_id} not found")
        
        # 2. Kiểm tra quyền sở hữu
        if card.user_id != user_id:
            raise PermissionError("Forbidden")
        
        # 3. Trả về thẻ
        return card


class ListDueCardsUseCase:
    """
    Ca sử dụng: Liệt kê các thẻ từ vựng đến hạn ôn tập.
    
    Quy trình:
    1. Gọi repository để lấy danh sách thẻ có next_review_at <= now
    2. Trả về danh sách thẻ
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(self, user_id: str) -> List[FlashCard]:
        """
        Thực thi trình tự lấy danh sách thẻ đến hạn.
        """
        return self._repo.list_due_cards(user_id)


class ListUserFlashcardsUseCase:
    """
    Ca sử dụng: Liệt kê tất cả thẻ từ vựng của người dùng với phân trang.
    
    Quy trình:
    1. Gọi repository để lấy danh sách thẻ với cursor-based pagination
    2. Trả về danh sách thẻ và cursor cho trang tiếp theo
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(
        self, user_id: str, last_key: Optional[dict], limit: int
    ) -> tuple[List[FlashCard], Optional[dict]]:
        """
        Thực thi trình tự lấy danh sách thẻ với phân trang.
        
        Returns:
            Tuple chứa (danh sách thẻ, cursor cho trang tiếp theo)
        """
        return self._repo.list_by_user(user_id, last_key, limit)


class ReviewFlashcardUseCase:
    """
    Ca sử dụng: Đánh giá mức độ nhớ thẻ từ vựng và cập nhật lịch ôn tập.
    
    Quy trình:
    1. Lấy thẻ từ repository theo user_id và flashcard_id
    2. Kiểm tra quyền sở hữu
    3. Áp dụng đánh giá SRS (forgot/hard/good/easy)
    4. Cập nhật thẻ vào database
    5. Trả về thẻ đã cập nhật
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(self, user_id: str, flashcard_id: str, rating: str) -> FlashCard:
        """
        Thực thi trình tự đánh giá thẻ từ vựng.
        
        Raises:
            KeyError: Nếu thẻ không tồn tại
            PermissionError: Nếu thẻ không thuộc về user
            ValueError: Nếu rating không hợp lệ
        """
        # 1. Lấy thẻ từ repository
        card = self._repo.get_by_user_and_id(user_id, flashcard_id)
        if card is None:
            raise KeyError(f"Flashcard {flashcard_id} not found")
        
        # 2. Kiểm tra quyền sở hữu
        if card.user_id != user_id:
            raise PermissionError("Forbidden")
        
        # 3. Áp dụng đánh giá SRS (raises ValueError nếu rating không hợp lệ)
        card.apply_sm2_review(rating)
        
        # 4. Cập nhật vào database
        self._repo.update(card)
        
        # 5. Trả về thẻ đã cập nhật
        return card


class UpdateFlashcardUseCase:
    """
    Ca sử dụng: Cập nhật nội dung thẻ từ vựng (translation, phonetic, example, audio).
    
    Quy trình:
    1. Lấy thẻ từ repository theo user_id và flashcard_id
    2. Kiểm tra quyền sở hữu
    3. Cập nhật các trường được cung cấp (partial update)
    4. Bảo tồn dữ liệu SRS (ease_factor, repetition_count, interval_days, next_review_at)
    5. Lưu thẻ đã cập nhật vào database
    6. Trả về thẻ đã cập nhật
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(
        self,
        user_id: str,
        flashcard_id: str,
        translation_vi: Optional[str] = None,
        phonetic: Optional[str] = None,
        audio_url: Optional[str] = None,
        example_sentence: Optional[str] = None
    ) -> FlashCard:
        """
        Thực thi trình tự cập nhật nội dung thẻ từ vựng.
        
        Raises:
            KeyError: Nếu thẻ không tồn tại
            PermissionError: Nếu thẻ không thuộc về user
        """
        # 1. Lấy thẻ từ repository
        card = self._repo.get_by_user_and_id(user_id, flashcard_id)
        if card is None:
            raise KeyError(f"Flashcard {flashcard_id} not found")
        
        # 2. Kiểm tra quyền sở hữu
        if card.user_id != user_id:
            raise PermissionError("Forbidden")
        
        # 3. Cập nhật các trường được cung cấp (partial update)
        if translation_vi is not None:
            card.translation_vi = translation_vi
        if phonetic is not None:
            card.phonetic = phonetic
        if audio_url is not None:
            card.audio_url = audio_url
        if example_sentence is not None:
            card.example_sentence = example_sentence
        
        # 4. SRS data được bảo tồn tự động (không cập nhật)
        
        # 5. Lưu thẻ đã cập nhật
        self._repo.save(card)
        
        # 6. Trả về thẻ đã cập nhật
        return card


class DeleteFlashcardUseCase:
    """
    Ca sử dụng: Xóa thẻ từ vựng.
    
    Quy trình:
    1. Lấy thẻ từ repository theo user_id và flashcard_id
    2. Kiểm tra quyền sở hữu
    3. Xóa thẻ khỏi database
    4. Trả về kết quả thành công
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(self, user_id: str, flashcard_id: str) -> bool:
        """
        Thực thi trình tự xóa thẻ từ vựng.
        
        Returns:
            True nếu xóa thành công
            
        Raises:
            KeyError: Nếu thẻ không tồn tại
            PermissionError: Nếu thẻ không thuộc về user
        """
        # 1. Lấy thẻ từ repository
        card = self._repo.get_by_user_and_id(user_id, flashcard_id)
        if card is None:
            raise KeyError(f"Flashcard {flashcard_id} not found")
        
        # 2. Kiểm tra quyền sở hữu
        if card.user_id != user_id:
            raise PermissionError("Forbidden")
        
        # 3. Xóa thẻ khỏi database
        # Note: Repository cần implement delete method
        if hasattr(self._repo, 'delete'):
            self._repo.delete(user_id, flashcard_id)
        else:
            raise NotImplementedError("Repository does not support delete operation")
        
        # 4. Trả về kết quả thành công
        return True



class ExportFlashcardsUseCase:
    """
    Ca sử dụng: Xuất tất cả thẻ từ vựng của người dùng dưới dạng JSON.
    
    Quy trình:
    1. Lấy danh sách tất cả thẻ của người dùng với cursor-based pagination
    2. Chuyển đổi thẻ thành định dạng JSON
    3. Trả về danh sách thẻ và cursor cho trang tiếp theo
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(
        self,
        user_id: str,
        cursor: Optional[str] = None,
        limit: int = 1000
    ) -> tuple[List[dict], Optional[str]]:
        """
        Thực thi trình tự xuất thẻ từ vựng.
        
        Returns:
            Tuple chứa (danh sách thẻ dạng dict, cursor cho trang tiếp theo)
        """
        # 1. Lấy danh sách thẻ từ repository
        cards, next_cursor = self._repo.list_by_user(user_id, cursor, limit)
        
        # 2. Chuyển đổi thẻ thành định dạng JSON
        exported_cards = [self._card_to_dict(card) for card in cards]
        
        # 3. Trả về danh sách thẻ và cursor
        return exported_cards, next_cursor
    
    @staticmethod
    def _card_to_dict(card: FlashCard) -> dict:
        """Chuyển đổi FlashCard entity thành dictionary."""
        return {
            "word": card.word,
            "translation_vi": card.translation_vi,
            "phonetic": card.phonetic,
            "audio_url": card.audio_url,
            "example_sentence": card.example_sentence,
            "ease_factor": card.ease_factor,
            "repetition_count": card.repetition_count,
            "interval_days": card.interval_days,
            "review_count": card.review_count,
            "last_reviewed_at": card.last_reviewed_at.isoformat() if card.last_reviewed_at else None,
            "next_review_at": card.next_review_at.isoformat(),
        }



class ImportFlashcardsUseCase:
    """
    Ca sử dụng: Nhập thẻ từ vựng từ JSON.
    
    Quy trình:
    1. Kiểm tra JSON schema
    2. Kiểm tra trùng lặp từ vựng
    3. Tạo thẻ mới cho từ vựng chưa tồn tại
    4. Trả về kết quả nhập (imported, skipped, failed)
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(self, user_id: str, flashcards_data: List[dict]) -> dict:
        """
        Thực thi trình tự nhập thẻ từ vựng.
        
        Returns:
            Dictionary với thống kê nhập (imported, skipped, failed, errors)
        """
        # Limit to 1000 flashcards per request
        if len(flashcards_data) > 1000:
            return {
                "imported": 0,
                "skipped": 0,
                "failed": len(flashcards_data),
                "errors": ["Import limit exceeded: maximum 1000 flashcards per request"]
            }
        
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        errors = []
        
        for idx, card_data in enumerate(flashcards_data):
            try:
                # Validate required fields
                word = card_data.get("word", "").strip()
                if not word:
                    errors.append(f"Item {idx}: Missing or empty word")
                    failed_count += 1
                    continue
                
                # Check for duplicates
                existing = self._repo.get_by_user_and_word(user_id, word)
                if existing:
                    skipped_count += 1
                    continue
                
                # Create new flashcard
                flashcard = FlashCard(
                    flashcard_id=str(ULID()),
                    user_id=user_id,
                    word=word,
                    translation_vi=card_data.get("translation_vi", ""),
                    phonetic=card_data.get("phonetic", ""),
                    audio_url=card_data.get("audio_url", ""),
                    example_sentence=card_data.get("example_sentence", ""),
                    ease_factor=float(card_data.get("ease_factor", 2.5)),
                    repetition_count=int(card_data.get("repetition_count", 0)),
                    interval_days=int(card_data.get("interval_days", 1)),
                    review_count=int(card_data.get("review_count", 0)),
                )
                
                # Save flashcard
                self._repo.save(flashcard)
                imported_count += 1
            
            except ValueError as e:
                errors.append(f"Item {idx}: {str(e)}")
                failed_count += 1
            except Exception as e:
                errors.append(f"Item {idx}: Unexpected error: {str(e)}")
                failed_count += 1
        
        return {
            "imported": imported_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "errors": errors
        }



class GetStatisticsUseCase:
    """
    Ca sử dụng: Lấy thống kê học tập của người dùng.
    
    Quy trình:
    1. Lấy tất cả thẻ của người dùng
    2. Tính toán các chỉ số thống kê
    3. Trả về kết quả
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(self, user_id: str) -> dict:
        """
        Thực thi trình tự lấy thống kê.
        
        Returns:
            Dictionary với các chỉ số thống kê
        """
        # Get all flashcards for user
        all_cards = []
        cursor = None
        while True:
            cards, cursor = self._repo.list_by_user(user_id, cursor, 1000)
            all_cards.extend(cards)
            if not cursor:
                break
        
        # Calculate statistics
        total_count = len(all_cards)
        
        # Count due today
        now = datetime.now(timezone.utc)
        due_today_count = sum(1 for card in all_cards if card.next_review_at <= now)
        
        # Count reviewed last 7 days
        seven_days_ago = now - timedelta(days=7)
        reviewed_last_7_days = sum(
            1 for card in all_cards
            if card.last_reviewed_at and card.last_reviewed_at >= seven_days_ago
        )
        
        # Count by maturity level
        new_count = sum(1 for card in all_cards if card.repetition_count == 0)
        learning_count = sum(1 for card in all_cards if 1 <= card.repetition_count <= 2)
        mature_count = sum(1 for card in all_cards if card.repetition_count >= 3)
        
        # Calculate average ease factor
        if total_count > 0:
            avg_ease_factor = sum(card.ease_factor for card in all_cards) / total_count
        else:
            avg_ease_factor = 2.5
        
        return {
            "total_count": total_count,
            "due_today_count": due_today_count,
            "reviewed_last_7_days": reviewed_last_7_days,
            "maturity_counts": {
                "new": new_count,
                "learning": learning_count,
                "mature": mature_count,
            },
            "average_ease_factor": round(avg_ease_factor, 2),
        }



class SearchFlashcardsUseCase:
    """
    Ca sử dụng: Tìm kiếm và lọc thẻ từ vựng.
    
    Quy trình:
    1. Lấy tất cả thẻ của người dùng
    2. Áp dụng các bộ lọc (word_prefix, min_interval, max_interval, maturity_level)
    3. Trả về kết quả với phân trang
    """
    
    def __init__(self, repo: FlashCardRepository):
        self._repo = repo
    
    def execute(
        self,
        user_id: str,
        word_prefix: Optional[str] = None,
        min_interval: Optional[int] = None,
        max_interval: Optional[int] = None,
        maturity_level: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 50
    ) -> tuple[List[dict], Optional[str], int]:
        """
        Thực thi trình tự tìm kiếm thẻ từ vựng.
        
        Returns:
            Tuple chứa (danh sách thẻ, cursor cho trang tiếp theo, tổng số kết quả)
        """
        # Get all flashcards for user
        all_cards = []
        search_cursor = None
        while True:
            cards, search_cursor = self._repo.list_by_user(user_id, search_cursor, 1000)
            all_cards.extend(cards)
            if not search_cursor:
                break
        
        # Apply filters
        filtered_cards = self._apply_filters(
            all_cards,
            word_prefix,
            min_interval,
            max_interval,
            maturity_level
        )
        
        total_count = len(filtered_cards)
        
        # Apply pagination
        start_idx = 0
        if cursor:
            try:
                start_idx = int(cursor)
            except (ValueError, TypeError):
                start_idx = 0
        
        end_idx = start_idx + limit
        paginated_cards = filtered_cards[start_idx:end_idx]
        
        # Convert to dict
        result_cards = [self._card_to_dict(card) for card in paginated_cards]
        
        # Calculate next cursor
        next_cursor = None
        if end_idx < total_count:
            next_cursor = str(end_idx)
        
        return result_cards, next_cursor, total_count
    
    @staticmethod
    def _apply_filters(
        cards: List[FlashCard],
        word_prefix: Optional[str] = None,
        min_interval: Optional[int] = None,
        max_interval: Optional[int] = None,
        maturity_level: Optional[str] = None
    ) -> List[FlashCard]:
        """Apply filters to flashcards."""
        filtered = cards
        
        # Filter by word prefix (case-insensitive)
        if word_prefix:
            prefix_lower = word_prefix.lower()
            filtered = [c for c in filtered if c.word.lower().startswith(prefix_lower)]
        
        # Filter by interval range
        if min_interval is not None:
            filtered = [c for c in filtered if c.interval_days >= min_interval]
        
        if max_interval is not None:
            filtered = [c for c in filtered if c.interval_days <= max_interval]
        
        # Filter by maturity level
        if maturity_level:
            if maturity_level == "new":
                filtered = [c for c in filtered if c.repetition_count == 0]
            elif maturity_level == "learning":
                filtered = [c for c in filtered if 1 <= c.repetition_count <= 2]
            elif maturity_level == "mature":
                filtered = [c for c in filtered if c.repetition_count >= 3]
        
        return filtered
    
    @staticmethod
    def _card_to_dict(card: FlashCard) -> dict:
        """Convert FlashCard to dictionary."""
        return {
            "flashcard_id": card.flashcard_id,
            "word": card.word,
            "translation_vi": card.translation_vi,
            "phonetic": card.phonetic,
            "audio_url": card.audio_url,
            "example_sentence": card.example_sentence,
            "ease_factor": card.ease_factor,
            "repetition_count": card.repetition_count,
            "interval_days": card.interval_days,
            "next_review_at": card.next_review_at.isoformat(),
        }
