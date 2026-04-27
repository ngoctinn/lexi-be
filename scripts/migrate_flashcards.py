#!/usr/bin/env python3
"""
Migration script to upgrade flashcards to SM-2 SRS schema.

This script:
1. Adds ease_factor=2.5 to all existing flashcards
2. Derives repetition_count from review_count using min(review_count, 3)
3. Adds GSI3PK and GSI3SK fields for efficient word lookup
4. Processes flashcards in batches of 25 to avoid DynamoDB throttling
5. Logs progress and errors to CloudWatch
6. Is idempotent (safe to run multiple times)
"""

import os
import sys
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AWS clients
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('logs')

TABLE_NAME = os.environ.get('LEXI_TABLE_NAME', 'LexiApp')
BATCH_SIZE = 25
LOG_GROUP = '/aws/lambda/flashcard-migration'
LOG_STREAM = f'migration-{datetime.now(timezone.utc).isoformat()}'


class FlashcardMigration:
    """Handles migration of flashcards to SM-2 schema."""
    
    def __init__(self, table_name: str = TABLE_NAME):
        self.table = dynamodb.Table(table_name)
        self.migrated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.errors: List[str] = []
    
    def migrate_flashcards(self) -> Dict[str, int]:
        """
        Execute migration in batches of 25 items.
        
        Returns:
            Dictionary with migration statistics
        """
        logger.info(f"Starting flashcard migration for table: {TABLE_NAME}")
        
        try:
            # Scan all flashcards
            items = self._scan_all_flashcards()
            logger.info(f"Found {len(items)} flashcards to migrate")
            
            # Process in batches
            for i in range(0, len(items), BATCH_SIZE):
                batch = items[i:i + BATCH_SIZE]
                self._process_batch(batch)
                logger.info(f"Processed batch {i // BATCH_SIZE + 1}: "
                           f"migrated={self.migrated_count}, "
                           f"skipped={self.skipped_count}, "
                           f"errors={self.error_count}")
            
            logger.info("Migration completed successfully")
            return {
                'migrated': self.migrated_count,
                'skipped': self.skipped_count,
                'errors': self.error_count,
                'total': len(items)
            }
        
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}", exc_info=True)
            raise
    
    def _scan_all_flashcards(self) -> List[Dict]:
        """Scan all flashcards from the table."""
        items = []
        last_key = None
        
        while True:
            kwargs = {
                'FilterExpression': 'EntityType = :et',
                'ExpressionAttributeValues': {':et': 'FLASHCARD'}
            }
            if last_key:
                kwargs['ExclusiveStartKey'] = last_key
            
            response = self.table.scan(**kwargs)
            items.extend(response.get('Items', []))
            
            last_key = response.get('LastEvaluatedKey')
            if not last_key:
                break
        
        return items
    
    def _process_batch(self, batch: List[Dict]) -> None:
        """Process a batch of flashcards."""
        with self.table.batch_writer(
            overwrite_by_pkeys=['PK', 'SK']
        ) as writer:
            for item in batch:
                try:
                    migrated_item = self._migrate_item(item)
                    if migrated_item:
                        writer.put_item(Item=migrated_item)
                        self.migrated_count += 1
                    else:
                        self.skipped_count += 1
                except Exception as e:
                    error_msg = f"Error migrating {item.get('flashcard_id')}: {str(e)}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
                    self.error_count += 1
    
    def _migrate_item(self, item: Dict) -> Optional[Dict]:
        """
        Migrate a single flashcard item.
        
        Returns:
            Migrated item or None if already migrated
        """
        # Check if already migrated (has ease_factor and repetition_count)
        if 'ease_factor' in item and 'repetition_count' in item:
            logger.debug(f"Skipping already migrated flashcard: {item.get('flashcard_id')}")
            return None
        
        # Add SM-2 fields
        item['ease_factor'] = 2.5
        item['repetition_count'] = self._derive_repetition_count(item.get('review_count', 0))
        
        # Add GSI3 fields for word lookup
        user_id = item.get('user_id')
        word = item.get('word', '')
        
        if user_id and word:
            item['GSI3PK'] = user_id
            item['GSI3SK'] = word.lower()
        else:
            logger.warning(f"Skipping item without user_id or word: {item.get('flashcard_id')}")
            return None
        
        # Update timestamp
        item['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        return item
    
    @staticmethod
    def _derive_repetition_count(review_count: int) -> int:
        """
        Derive repetition_count from existing review_count.
        
        Conservative approach: assume max 3 consecutive successes.
        This ensures ease_factor doesn't become unreasonably high.
        """
        return min(review_count, 3)
    
    def validate_migration(self) -> Tuple[bool, Dict[str, any]]:
        """
        Validate that migration was successful.
        
        Returns:
            Tuple of (success: bool, validation_results: dict)
        """
        logger.info("Validating migration...")
        
        validation_results = {
            'total_flashcards': 0,
            'with_ease_factor': 0,
            'with_repetition_count': 0,
            'with_gsi3_fields': 0,
            'missing_ease_factor': [],
            'missing_repetition_count': [],
            'missing_gsi3_fields': []
        }
        
        try:
            items = self._scan_all_flashcards()
            validation_results['total_flashcards'] = len(items)
            
            for item in items:
                if 'ease_factor' in item:
                    validation_results['with_ease_factor'] += 1
                else:
                    validation_results['missing_ease_factor'].append(item.get('flashcard_id'))
                
                if 'repetition_count' in item:
                    validation_results['with_repetition_count'] += 1
                else:
                    validation_results['missing_repetition_count'].append(item.get('flashcard_id'))
                
                if 'GSI3PK' in item and 'GSI3SK' in item:
                    validation_results['with_gsi3_fields'] += 1
                else:
                    validation_results['missing_gsi3_fields'].append(item.get('flashcard_id'))
            
            # Check if all flashcards were migrated
            success = (
                validation_results['with_ease_factor'] == len(items) and
                validation_results['with_repetition_count'] == len(items) and
                validation_results['with_gsi3_fields'] == len(items)
            )
            
            if success:
                logger.info("✓ Migration validation passed")
            else:
                logger.warning("✗ Migration validation failed")
                logger.warning(f"  Missing ease_factor: {len(validation_results['missing_ease_factor'])}")
                logger.warning(f"  Missing repetition_count: {len(validation_results['missing_repetition_count'])}")
                logger.warning(f"  Missing GSI3 fields: {len(validation_results['missing_gsi3_fields'])}")
            
            return success, validation_results
        
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}", exc_info=True)
            return False, validation_results


def main():
    """Main entry point for migration script."""
    try:
        migration = FlashcardMigration()
        
        # Execute migration
        stats = migration.migrate_flashcards()
        logger.info(f"Migration statistics: {stats}")
        
        # Validate migration
        success, validation = migration.validate_migration()
        logger.info(f"Validation results: {validation}")
        
        if success:
            logger.info("✓ Migration completed successfully")
            return 0
        else:
            logger.error("✗ Migration validation failed")
            return 1
    
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
