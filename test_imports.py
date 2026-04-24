#!/usr/bin/env python3
"""Test actual imports by trying to import each handler."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

handlers = [
    ('websocket_handler', 'infrastructure.handlers.websocket_handler'),
    ('session_handler', 'infrastructure.handlers.session_handler'),
    ('create_flashcard_handler', 'infrastructure.handlers.flashcard.create_flashcard_handler'),
    ('list_due_cards_handler', 'infrastructure.handlers.flashcard.list_due_cards_handler'),
    ('get_flashcard_handler', 'infrastructure.handlers.flashcard.get_flashcard_handler'),
    ('list_flashcards_handler', 'infrastructure.handlers.flashcard.list_flashcards_handler'),
    ('review_flashcard_handler', 'infrastructure.handlers.flashcard.review_flashcard_handler'),
]

print("🔍 Testing handler imports...\n")

errors = []
for name, module_path in handlers:
    try:
        __import__(module_path)
        print(f"✅ {name}")
    except ImportError as e:
        error_msg = f"❌ {name}: ImportError: {str(e)}"
        print(error_msg)
        errors.append(error_msg)
    except Exception as e:
        error_msg = f"❌ {name}: {type(e).__name__}: {str(e)}"
        print(error_msg)
        errors.append(error_msg)

print()
if errors:
    print(f"❌ Found {len(errors)} errors:\n")
    for error in errors:
        print(f"  {error}")
    sys.exit(1)
else:
    print("✅ All handlers import successfully!")
    sys.exit(0)
