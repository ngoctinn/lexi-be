#!/usr/bin/env python3
"""Test vocabulary translation to reproduce the issue."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from application.dtos.vocabulary_dtos import TranslateVocabularyCommand
from infrastructure.service_factory import ServiceFactory

def test_translate_vocabulary():
    """Test vocabulary translation with real services."""
    print("\n" + "="*60)
    print("TEST: Vocabulary Translation")
    print("="*60)
    
    try:
        # Create services
        print("\n📦 Creating services...")
        translate_service = ServiceFactory.create_translation_service()
        dictionary_service = ServiceFactory.create_dictionary_service()
        
        # Create use case
        use_case = TranslateVocabularyUseCase(
            dictionary_service=dictionary_service,
            translation_service=translate_service
        )
        
        # Test word
        test_word = "run"
        print(f"\n📤 Translating word: '{test_word}'")
        
        # Execute
        command = TranslateVocabularyCommand(word=test_word)
        result = use_case.execute(command)
        
        if result.is_success:
            response = result.value
            print(f"\n✅ Translation successful!")
            print(f"  Word: {response.word}")
            print(f"  Translation: {response.translate_vi}")
            print(f"  Phonetic: {response.phonetic}")
            print(f"  Meanings count: {len(response.meanings)}")
            print(f"  Response time: {response.response_time_ms}ms")
            
            if response.meanings:
                print(f"\n📝 Meanings:")
                for i, meaning in enumerate(response.meanings):
                    print(f"\n  Meaning {i+1} ({meaning.part_of_speech}):")
                    print(f"    Definition (EN): {meaning.definition}")
                    print(f"    Definition (VI): {meaning.definition_vi}")
                    if meaning.example:
                        print(f"    Example (EN): {meaning.example}")
                        print(f"    Example (VI): {meaning.example_vi}")
            
            return True
        else:
            print(f"\n❌ Translation failed!")
            print(f"  Error: {result.error}")
            return False
        
    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_translate_vocabulary()
    exit(0 if success else 1)
