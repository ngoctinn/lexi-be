#!/usr/bin/env python3
"""Test phrasal verb detection and translation."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging

# Enable debug logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from application.dtos.vocabulary_dtos import TranslateVocabularyCommand
from infrastructure.service_factory import ServiceFactory


def test_phrasal_verb(word, context):
    """Test phrasal verb detection."""
    print("\n" + "="*60)
    print(f"TEST: Phrasal Verb Detection")
    print("="*60)
    
    try:
        # Create services
        translate_service = ServiceFactory.create_translation_service()
        dictionary_service = ServiceFactory.create_dictionary_service()
        
        # Create use case
        use_case = TranslateVocabularyUseCase(
            dictionary_service=dictionary_service,
            translation_service=translate_service
        )
        
        print(f"\n📤 Word: '{word}'")
        print(f"📝 Context: '{context}'")
        
        # Execute with context
        command = TranslateVocabularyCommand(word=word, context=context)
        result = use_case.execute(command)
        
        if result.is_success:
            response = result.value
            print(f"\n✅ Translation successful!")
            print(f"  Detected word: {response.word}")
            print(f"  Translation: {response.translate_vi}")
            print(f"  Phonetic: {response.phonetic}")
            print(f"  Response time: {response.response_time_ms}ms")
            
            if response.meanings:
                print(f"\n📚 Meanings ({len(response.meanings)}):")
                for i, meaning in enumerate(response.meanings):
                    print(f"\n  [{i+1}] {meaning.part_of_speech}")
                    print(f"      Definition (EN): {meaning.definition}")
                    print(f"      Definition (VI): {meaning.definition_vi}")
                    if meaning.example:
                        print(f"      Example (EN): {meaning.example}")
                        print(f"      Example (VI): {meaning.example_vi}")
            
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


def main():
    """Run phrasal verb tests."""
    print("\n" + "="*60)
    print("PHRASAL VERB DETECTION TESTS")
    print("="*60)
    
    test_cases = [
        {
            "word": "get",
            "context": "I need to get off the bus",
            "expected": "get off (xuống xe)"
        },
        {
            "word": "get",
            "context": "I get up at 6 AM every day",
            "expected": "get up (thức dậy)"
        },
        {
            "word": "run",
            "context": "I run into my friend yesterday",
            "expected": "run into (tình cờ gặp)"
        },
        {
            "word": "look",
            "context": "Can you look after my dog?",
            "expected": "look after (chăm sóc)"
        },
        {
            "word": "get",
            "context": "I get a book from the library",
            "expected": "get (lấy, nhận) - NOT phrasal verb"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"Test Case {i+1}/{len(test_cases)}")
        print(f"Expected: {test['expected']}")
        print(f"{'='*60}")
        
        success = test_phrasal_verb(test["word"], test["context"])
        results.append({
            "test": test,
            "success": success
        })
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for i, result in enumerate(results):
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        test = result["test"]
        print(f"\n{status} Test {i+1}: {test['word']} in '{test['context'][:40]}...'")
        print(f"     Expected: {test['expected']}")
    
    total = len(results)
    passed = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} passed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
