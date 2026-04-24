#!/usr/bin/env python3
"""
Migration script: Set assigned_model for existing sessions based on proficiency level.

Usage:
    python scripts/migrate_assigned_model.py [--dry-run] [--limit N]

Options:
    --dry-run: Show what would be updated without making changes
    --limit N: Only process first N sessions (default: all)
"""

import os
import sys
import argparse
import logging
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from domain.services.model_router import ModelRouter
from domain.value_objects.enums import ProficiencyLevel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_dynamodb_table():
    """Get DynamoDB table for sessions."""
    table_name = os.environ.get('LEXI_TABLE_NAME')
    if not table_name:
        raise ValueError("LEXI_TABLE_NAME environment variable not set")
    
    dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(table_name)


def migrate_sessions(dry_run=False, limit=None):
    """
    Migrate existing sessions by setting assigned_model based on level.
    
    Args:
        dry_run: If True, only show what would be updated
        limit: Maximum number of sessions to process
    """
    table = get_dynamodb_table()
    
    # Scan all sessions
    logger.info("Scanning sessions...")
    
    processed = 0
    updated = 0
    skipped = 0
    errors = 0
    
    scan_kwargs = {
        'FilterExpression': Attr('EntityType').eq('SESSION')
    }
    
    try:
        while True:
            response = table.scan(**scan_kwargs)
            
            for item in response.get('Items', []):
                if limit and processed >= limit:
                    logger.info(f"Reached limit of {limit} sessions")
                    break
                
                try:
                    session_id = item.get('session_id')
                    level = item.get('level')
                    assigned_model = item.get('assigned_model', '')
                    
                    # Skip if already has assigned_model
                    if assigned_model:
                        logger.debug(f"Session {session_id} already has assigned_model: {assigned_model}")
                        skipped += 1
                        processed += 1
                        continue
                    
                    # Get primary model for this level
                    try:
                        primary_model = ModelRouter.get_primary_model(level)
                    except ValueError as e:
                        logger.warning(f"Session {session_id}: Invalid level '{level}': {e}")
                        errors += 1
                        processed += 1
                        continue
                    
                    logger.info(f"Session {session_id} (level={level}): assigned_model={primary_model}")
                    
                    if not dry_run:
                        # Update session with assigned_model
                        table.update_item(
                            Key={
                                'PK': f"SESSION#{session_id}",
                                'SK': 'METADATA'
                            },
                            UpdateExpression='SET assigned_model = :model, updated_at = :now',
                            ExpressionAttributeValues={
                                ':model': primary_model,
                                ':now': item.get('updated_at', '')  # Keep existing timestamp
                            }
                        )
                    
                    updated += 1
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing session {item.get('session_id')}: {e}")
                    errors += 1
                    processed += 1
            
            # Check for more items
            if 'LastEvaluatedKey' not in response or (limit and processed >= limit):
                break
            
            scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
    
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return False
    
    # Summary
    logger.info("=" * 60)
    logger.info("Migration Summary:")
    logger.info(f"  Total processed: {processed}")
    logger.info(f"  Updated: {updated}")
    logger.info(f"  Skipped (already set): {skipped}")
    logger.info(f"  Errors: {errors}")
    logger.info(f"  Dry run: {dry_run}")
    logger.info("=" * 60)
    
    return errors == 0


def main():
    parser = argparse.ArgumentParser(
        description='Migrate assigned_model for existing sessions'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Only process first N sessions'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting migration (dry_run={args.dry_run}, limit={args.limit})")
    
    success = migrate_sessions(dry_run=args.dry_run, limit=args.limit)
    
    if success:
        logger.info("Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("Migration completed with errors")
        sys.exit(1)


if __name__ == '__main__':
    main()
