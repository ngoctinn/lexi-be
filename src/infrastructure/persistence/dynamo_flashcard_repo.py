from datetime import datetime, timedelta, timezone
from typing import List, Optional
import os

import boto3

from application.repositories.flash_card_repository import FlashCardRepository
from domain.entities.flashcard import FlashCard


class DynamoFlashCardRepository(FlashCardRepository):
    """Lưu trữ flashcard trong DynamoDB."""

    def __init__(self, table=None):
        self._table = table or boto3.resource("dynamodb").Table(os.environ["LEXI_TABLE_NAME"])

    def save(self, card: FlashCard) -> None:
        """Lưu hoặc cập nhật flashcard."""
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "PK": f"FLASHCARD#{card.user_id}",
            "SK": f"CARD#{card.flashcard_id}",
            "EntityType": "FLASHCARD",
            "flashcard_id": card.flashcard_id,
            "user_id": card.user_id,
            "word": card.word,
            "translation_vi": card.translation_vi,
            "definition_vi": card.definition_vi,
            "phonetic": card.phonetic,
            "audio_url": card.audio_url,
            "example_sentence": card.example_sentence,
            "review_count": card.review_count,
            "interval_days": card.interval_days,
            "difficulty": card.difficulty,
            "last_reviewed_at": card.last_reviewed_at.isoformat() if card.last_reviewed_at else None,
            "next_review_at": card.next_review_at.isoformat(),
            "created_at": now,
            "updated_at": now,
        }
        
        # Thêm source tracking nếu có
        if card.source_session_id:
            item["source_session_id"] = card.source_session_id
        if card.source_turn_index is not None:
            item["source_turn_index"] = card.source_turn_index
            
        self._table.put_item(Item=item)

    def get_by_id(self, flashcard_id: str) -> Optional[FlashCard]:
        """Truy xuất flashcard theo ID."""
        # Cần user_id để query, nên không thể implement đơn giản
        # Thường dùng GSI hoặc scan
        raise NotImplementedError("Sử dụng get_by_user_and_word thay vào đó.")

    def list_due_cards(self, user_id: str) -> List[FlashCard]:
        """Lấy danh sách flashcard đến hạn ôn tập."""
        now = datetime.now(timezone.utc).isoformat()
        response = self._table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": f"FLASHCARD#{user_id}",
                ":sk_prefix": "CARD#",
            },
        )

        items = response.get("Items", [])
        cards = []
        for item in items:
            card = self._to_entity(item)
            # Chỉ lấy thẻ đã đến hạn ôn tập
            if card.next_review_at.isoformat() <= now:
                cards.append(card)

        return cards

    def get_by_user_and_word(self, user_id: str, word: str) -> Optional[FlashCard]:
        """Kiểm tra xem người dùng đã có thẻ cho từ này chưa."""
        # Cần scan hoặc GSI vì word không phải key
        # Tạm thời trả về None để cho phép tạo mới
        # TODO: Implement GSI hoặc scan nếu cần check trùng lặp
        return None

    def _to_entity(self, item: dict) -> FlashCard:
        """Chuyển đổi DynamoDB item thành FlashCard entity."""
        last_reviewed = None
        if item.get("last_reviewed_at"):
            last_reviewed = datetime.fromisoformat(item["last_reviewed_at"])

        next_review = datetime.fromisoformat(item["next_review_at"])

        return FlashCard(
            flashcard_id=item.get("flashcard_id", ""),
            user_id=item.get("user_id", ""),
            word=item.get("word", ""),
            translation_vi=item.get("translation_vi", ""),
            definition_vi=item.get("definition_vi", ""),
            phonetic=item.get("phonetic", ""),
            audio_url=item.get("audio_url", ""),
            example_sentence=item.get("example_sentence", ""),
            review_count=item.get("review_count", 0),
            interval_days=item.get("interval_days", 1),
            difficulty=item.get("difficulty", 0),
            last_reviewed_at=last_reviewed,
            next_review_at=next_review,
            source_session_id=item.get("source_session_id"),
            source_turn_index=item.get("source_turn_index"),
        )
