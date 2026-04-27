"""Unit tests for flashcard migration logic."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Import migration script
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../scripts'))
from migrate_flashcards import FlashcardMigration


class TestFlashcardMigration:
    """Unit tests for flashcard migration."""
    
    @pytest.fixture
    def migration(self):
        """Create a migration instance with mocked table."""
        with patch('migrate_flashcards.dynamodb'):
            migration = FlashcardMigration()
            migration.table = MagicMock()
            return migration
    
    def test_derive_repetition_count(self):
        """Test that repetition_count is derived correctly from review_count."""
        # Test various review counts
        assert FlashcardMigration._derive_repetition_count(0) == 0
        assert FlashcardMigration._derive_repetition_count(1) == 1
        assert FlashcardMigration._derive_repetition_count(2) == 2
        assert FlashcardMigration._derive_repetition_count(3) == 3
        assert FlashcardMigration._derive_repetition_count(4) == 3  # Capped at 3
        assert FlashcardMigration._derive_repetition_count(10) == 3  # Capped at 3
    
    def test_migrate_item_adds_ease_factor(self, migration):
        """Test that migration adds ease_factor=2.5."""
        item = {
            'flashcard_id': 'card-001',
            'user_id': 'user-001',
            'word': 'example',
            'review_count': 5
        }
        
        migrated = migration._migrate_item(item)
        
        assert migrated is not None
        assert migrated['ease_factor'] == 2.5
    
    def test_migrate_item_adds_repetition_count(self, migration):
        """Test that migration adds repetition_count derived from review_count."""
        item = {
            'flashcard_id': 'card-001',
            'user_id': 'user-001',
            'word': 'example',
            'review_count': 5
        }
        
        migrated = migration._migrate_item(item)
        
        assert migrated is not None
        assert migrated['repetition_count'] == 3  # min(5, 3)
    
    def test_migrate_item_adds_gsi3_fields(self, migration):
        """Test that migration adds GSI3PK and GSI3SK."""
        item = {
            'flashcard_id': 'card-001',
            'user_id': 'user-001',
            'word': 'Example',
            'review_count': 0
        }
        
        migrated = migration._migrate_item(item)
        
        assert migrated is not None
        assert migrated['GSI3PK'] == 'user-001'
        assert migrated['GSI3SK'] == 'example'  # Lowercase
    
    def test_migrate_item_skips_already_migrated(self, migration):
        """Test that already migrated items are skipped."""
        item = {
            'flashcard_id': 'card-001',
            'user_id': 'user-001',
            'word': 'example',
            'ease_factor': 2.5,
            'repetition_count': 2
        }
        
        migrated = migration._migrate_item(item)
        
        assert migrated is None  # Should skip
    
    def test_migrate_item_skips_missing_user_id(self, migration):
        """Test that items without user_id are skipped."""
        item = {
            'flashcard_id': 'card-001',
            'word': 'example',
            'review_count': 0
        }
        
        migrated = migration._migrate_item(item)
        
        assert migrated is None  # Should skip
    
    def test_migrate_item_skips_missing_word(self, migration):
        """Test that items without word are skipped."""
        item = {
            'flashcard_id': 'card-001',
            'user_id': 'user-001',
            'review_count': 0
        }
        
        migrated = migration._migrate_item(item)
        
        assert migrated is None  # Should skip
    
    def test_migrate_item_updates_timestamp(self, migration):
        """Test that migration updates the updated_at timestamp."""
        item = {
            'flashcard_id': 'card-001',
            'user_id': 'user-001',
            'word': 'example',
            'review_count': 0,
            'updated_at': '2020-01-01T00:00:00+00:00'
        }
        
        before = datetime.now(timezone.utc)
        migrated = migration._migrate_item(item)
        after = datetime.now(timezone.utc)
        
        assert migrated is not None
        updated_at = datetime.fromisoformat(migrated['updated_at'])
        assert before <= updated_at <= after
    
    def test_batch_processing(self, migration):
        """Test that batch processing works correctly."""
        items = [
            {
                'flashcard_id': f'card-{i:03d}',
                'user_id': 'user-001',
                'word': f'word{i}',
                'review_count': i
            }
            for i in range(5)
        ]
        
        migration._process_batch(items)
        
        # Verify batch writer was used
        assert migration.migrated_count == 5
        assert migration.error_count == 0
    
    def test_migration_statistics(self, migration):
        """Test that migration statistics are tracked correctly."""
        assert migration.migrated_count == 0
        assert migration.skipped_count == 0
        assert migration.error_count == 0
        
        # Simulate migration
        migration.migrated_count = 10
        migration.skipped_count = 2
        migration.error_count = 1
        
        assert migration.migrated_count == 10
        assert migration.skipped_count == 2
        assert migration.error_count == 1
    
    def test_word_normalization_in_migration(self, migration):
        """Test that words are normalized to lowercase in GSI3SK."""
        test_cases = [
            ('Example', 'example'),
            ('EXAMPLE', 'example'),
            ('ExAmPlE', 'example'),
            ('example', 'example'),
        ]
        
        for word, expected_gsi3sk in test_cases:
            item = {
                'flashcard_id': 'card-001',
                'user_id': 'user-001',
                'word': word,
                'review_count': 0
            }
            
            migrated = migration._migrate_item(item)
            
            assert migrated is not None
            assert migrated['GSI3SK'] == expected_gsi3sk, f"Word '{word}' should normalize to '{expected_gsi3sk}'"
