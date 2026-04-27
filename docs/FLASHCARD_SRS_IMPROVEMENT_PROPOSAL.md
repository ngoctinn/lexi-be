# Flashcard SRS Algorithm Improvement Proposal

**Date:** 2026-04-27  
**Status:** DRAFT  
**Priority:** HIGH (Algorithm correctness issue)

---

## 🎯 Executive Summary

Current flashcard SRS implementation **does not follow SM-2 algorithm correctly**, leading to suboptimal learning intervals and poor retention rates. This proposal outlines a complete fix to implement proper SM-2 algorithm.

---

## ⚠️ Current Issues

### 1. **Incorrect SRS Algorithm**
- Missing Ease Factor (EF) - core component of SM-2
- Wrong interval calculation formulas
- No special handling for first 2 reviews
- Incorrect "forgot" reset logic

### 2. **Missing Database Fields**
- No `ease_factor` field (should be 1.3-2.5)
- `difficulty` field (0-5) is not the same as ease_factor

### 3. **Inefficient Queries**
- `get_by_user_and_word` uses SCAN instead of GSI
- Will not scale with large datasets

### 4. **Missing Endpoints**
- No DELETE flashcard
- No UPDATE flashcard
- No statistics/progress tracking
- No search/filter capabilities

---

## 💡 Proposed Solution

### **Phase 1: Fix SRS Algorithm (Week 1)**

#### 1.1 Update Entity

```python
@dataclass
class FlashCard:
    # ... existing fields ...
    
    # SRS fields (SM-2 compliant)
    ease_factor: float = 2.5  # NEW: 1.3-2.5 range
    repetition_count: int = 0  # NEW: Track review count
    interval_days: int = 1
    last_reviewed_at: Optional[datetime] = None
    next_review_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Remove or deprecate
    # difficulty: int = 0  # DEPRECATED - not used in SM-2

    def apply_review_sm2(self, quality: int) -> None:
        """
        Apply SM-2 algorithm correctly.
        
        Args:
            quality: 0-5 scale
                0 = Complete blackout
                1 = Incorrect, but correct answer seemed familiar
                2 = Incorrect, but correct answer seemed easy to recall
                3 = Correct, but with serious difficulty
                4 = Correct, after some hesitation
                5 = Perfect response
        """
        now = datetime.now(timezone.utc)
        
        # Validate quality
        quality = max(0, min(5, quality))
        
        # SM-2 Algorithm
        if quality < 3:
            # Failed - reset to beginning
            self.repetition_count = 0
            self.interval_days = 1
        else:
            # Passed - calculate new interval
            if self.repetition_count == 0:
                self.interval_days = 1
            elif self.repetition_count == 1:
                self.interval_days = 6
            else:
                self.interval_days = round(self.interval_days * self.ease_factor)
            
            self.repetition_count += 1
        
        # Update ease factor (SM-2 formula)
        ease_change = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        self.ease_factor = max(1.3, self.ease_factor + ease_change)
        
        # Update timestamps
        self.last_reviewed_at = now
        self.next_review_at = now + timedelta(days=self.interval_days)
        
    def map_rating_to_quality(self, rating: str) -> int:
        """Map string rating to SM-2 quality (0-5)."""
        mapping = {
            "forgot": 0,      # Complete blackout
            "hard": 3,        # Correct with serious difficulty
            "good": 4,        # Correct after hesitation
            "easy": 5,        # Perfect response
        }
        return mapping.get(rating, 3)
```

#### 1.2 Update Repository

```python
class DynamoFlashCardRepository(FlashCardRepository):
    def save(self, card: FlashCard) -> None:
        """Save with new ease_factor field."""
        item = {
            # ... existing fields ...
            "ease_factor": Decimal(str(card.ease_factor)),  # NEW
            "repetition_count": card.repetition_count,      # NEW
            # ... rest of fields ...
        }
        self._table.put_item(Item=item)
    
    def _to_entity(self, item: dict) -> FlashCard:
        """Convert with new fields."""
        return FlashCard(
            # ... existing fields ...
            ease_factor=float(item.get("ease_factor", 2.5)),
            repetition_count=item.get("repetition_count", 0),
            # ... rest of fields ...
        )
```

#### 1.3 Update Handler

```python
# review_flashcard_handler.py
def handler(event, context):
    # ... auth logic ...
    
    body = json.loads(event.get("body", "{}"))
    rating = body.get("rating")  # "forgot" | "hard" | "good" | "easy"
    
    # Map to SM-2 quality
    quality = card.map_rating_to_quality(rating)
    
    # Apply SM-2 algorithm
    card.apply_review_sm2(quality)
    
    # Save
    repo.update(card)
```

---

### **Phase 2: Add GSI for Word Lookup (Week 1)**

#### 2.1 Update DynamoDB Schema

```yaml
# config/database.yaml
GlobalSecondaryIndexes:
  # ... existing GSIs ...
  
  # GSI3: Word lookup by user
  - IndexName: GSI3-UserWord-Lookup
    KeySchema:
      - AttributeName: GSI3PK
        KeyType: HASH
      - AttributeName: GSI3SK
        KeyType: RANGE
    Projection:
      ProjectionType: ALL
    ProvisionedThroughput:
      ReadCapacityUnits: 5
      WriteCapacityUnits: 5
```

#### 2.2 Update Repository

```python
def save(self, card: FlashCard) -> None:
    item = {
        # ... existing fields ...
        "GSI3PK": f"{card.user_id}#WORD",
        "GSI3SK": card.word.lower(),
    }
    self._table.put_item(Item=item)

def get_by_user_and_word(self, user_id: str, word: str) -> Optional[FlashCard]:
    """Use GSI instead of SCAN."""
    response = self._table.query(
        IndexName="GSI3-UserWord-Lookup",
        KeyConditionExpression=Key("GSI3PK").eq(f"{user_id}#WORD") & Key("GSI3SK").eq(word.lower()),
        Limit=1
    )
    items = response.get("Items", [])
    return self._to_entity(items[0]) if items else None
```

---

### **Phase 3: Add Missing Endpoints (Week 2)**

#### 3.1 DELETE Flashcard

```python
# delete_flashcard_handler.py
def handler(event, context):
    user_id = extract_user_id(event)
    flashcard_id = event["pathParameters"]["flashcard_id"]
    
    # Get card to verify ownership
    card = repo.get_by_user_and_id(user_id, flashcard_id)
    if not card:
        return error_response(404, "Flashcard not found")
    
    if card.user_id != user_id:
        return error_response(403, "Forbidden")
    
    # Delete
    repo.delete(user_id, flashcard_id)
    
    return success_response(200, {"message": "Flashcard deleted"})
```

**Add to template.yaml:**
```yaml
DeleteFlashcardFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: infrastructure.handlers.flashcard.delete_flashcard_handler.handler
    Events:
      DeleteFlashcard:
        Type: Api
        Properties:
          Path: /flashcards/{flashcard_id}
          Method: DELETE
          RestApiId: !Ref LexiApi
```

#### 3.2 UPDATE Flashcard

```python
# update_flashcard_handler.py
def handler(event, context):
    user_id = extract_user_id(event)
    flashcard_id = event["pathParameters"]["flashcard_id"]
    body = json.loads(event["body"])
    
    # Get card
    card = repo.get_by_user_and_id(user_id, flashcard_id)
    if not card or card.user_id != user_id:
        return error_response(404, "Not found")
    
    # Update allowed fields
    if "translation_vi" in body:
        card.translation_vi = body["translation_vi"]
    if "example_sentence" in body:
        card.example_sentence = body["example_sentence"]
    if "phonetic" in body:
        card.phonetic = body["phonetic"]
    
    repo.update(card)
    return success_response(200, card.to_dict())
```

#### 3.3 Statistics Endpoint

```python
# get_flashcard_stats_handler.py
def handler(event, context):
    user_id = extract_user_id(event)
    
    stats = {
        "total_cards": repo.count_by_user(user_id),
        "due_today": len(repo.list_due_cards(user_id)),
        "mastered": repo.count_mastered(user_id),  # ease_factor > 2.5, interval > 30
        "learning": repo.count_learning(user_id),  # repetition_count < 3
        "review": repo.count_review(user_id),      # repetition_count >= 3
    }
    
    return success_response(200, stats)
```

---

### **Phase 4: Data Migration (Week 2)**

#### 4.1 Migration Script

```python
# scripts/migrate_flashcards_to_sm2.py
import boto3
from decimal import Decimal

def migrate_flashcards():
    """Add ease_factor and repetition_count to existing cards."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('LexiAppTable')
    
    # Scan all flashcards
    response = table.scan(
        FilterExpression="EntityType = :type",
        ExpressionAttributeValues={":type": "FLASHCARD"}
    )
    
    for item in response['Items']:
        # Add new fields
        table.update_item(
            Key={
                "PK": item["PK"],
                "SK": item["SK"]
            },
            UpdateExpression="""
                SET ease_factor = :ef,
                    repetition_count = :rc,
                    GSI3PK = :gsi3pk,
                    GSI3SK = :gsi3sk
            """,
            ExpressionAttributeValues={
                ":ef": Decimal("2.5"),  # Default ease factor
                ":rc": item.get("review_count", 0),  # Use existing review_count
                ":gsi3pk": f"{item['user_id']}#WORD",
                ":gsi3sk": item["word"].lower(),
            }
        )
    
    print(f"Migrated {len(response['Items'])} flashcards")

if __name__ == "__main__":
    migrate_flashcards()
```

---

## 📊 Expected Impact

### **Before Fix:**
- ❌ Incorrect intervals (too short or too long)
- ❌ Poor retention rates
- ❌ Inefficient reviews
- ❌ Slow queries (SCAN)

### **After Fix:**
- ✅ Correct SM-2 algorithm
- ✅ Optimal learning intervals
- ✅ Better retention (85%+ target)
- ✅ Fast queries (GSI)
- ✅ Complete CRUD operations

---

## 🚀 Implementation Plan

### **Week 1: Core Algorithm Fix**
- [ ] Day 1-2: Update entity with ease_factor
- [ ] Day 3-4: Implement correct SM-2 algorithm
- [ ] Day 4-5: Add GSI3 for word lookup
- [ ] Day 5: Write tests

### **Week 2: Missing Features**
- [ ] Day 1-2: Add DELETE endpoint
- [ ] Day 2-3: Add UPDATE endpoint
- [ ] Day 3-4: Add statistics endpoint
- [ ] Day 4-5: Data migration script

### **Week 3: Testing & Deployment**
- [ ] Day 1-2: Integration testing
- [ ] Day 3: Deploy to staging
- [ ] Day 4: Run migration script
- [ ] Day 5: Deploy to production

---

## 🧪 Testing Strategy

### **Unit Tests**
```python
def test_sm2_algorithm():
    card = FlashCard(...)
    
    # Test first review (quality=4)
    card.apply_review_sm2(4)
    assert card.interval_days == 1
    assert card.repetition_count == 1
    
    # Test second review (quality=4)
    card.apply_review_sm2(4)
    assert card.interval_days == 6
    assert card.repetition_count == 2
    
    # Test third review (quality=4)
    card.apply_review_sm2(4)
    assert card.interval_days == round(6 * card.ease_factor)
    
    # Test forgot (quality=0)
    card.apply_review_sm2(0)
    assert card.interval_days == 1
    assert card.repetition_count == 0
```

### **Integration Tests**
- Test full review flow with correct intervals
- Test GSI query performance
- Test CRUD operations
- Test statistics calculation

---

## 📚 References

1. **SM-2 Algorithm Original Paper**
   - https://www.supermemo.com/en/archives1990-2015/english/ol/sm2

2. **Anki's SM-2 Implementation**
   - https://faqs.ankiweb.net/what-spaced-repetition-algorithm.html

3. **FSRS (Modern Alternative)**
   - https://github.com/open-spaced-repetition/fsrs-rs
   - Consider for future upgrade

---

## ✅ Success Criteria

- [ ] SM-2 algorithm implemented correctly
- [ ] All tests passing
- [ ] GSI query < 100ms
- [ ] Retention rate > 85%
- [ ] Zero data loss during migration
- [ ] All CRUD operations working

---

**Status:** Ready for review and approval
**Next Steps:** Get stakeholder approval → Start Week 1 implementation
