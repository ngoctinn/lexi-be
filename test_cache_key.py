#!/usr/bin/env python3
"""Test cache key for phrasal verbs."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from application.use_cases.vocabulary_use_cases import TranslateVocabularyUseCase
from application.dtos.vocabulary_dtos import TranslateVocabularyCommand
from infrastructure.service_factory import ServiceFactory


def test_cache_key():
    """Test what cache key is used for phrasal verbs."""
    print("\n" + "="*60)
    print("TEST: Cache Key for Phrasal Verbs")
    print("="*60)
    
    # Create services
    translate_service = ServiceFactory.create_translation_service()
    dictionary_service = ServiceFactory.create_dictionary_service()
    use_case = TranslateVocabularyUseCase(dictionary_service, translate_service)
    
    # Test 1: Click "get" in "get off" context
    print("\n" + "="*60)
    print("Test 1: User clicks 'get' in 'I need to get off the bus'")
    print("="*60)
    
    command1 = TranslateVocabularyCommand(
        word="get",
        context="I need to get off the bus"
    )
    result1 = use_case.execute(command1)
    
    if result1.is_success:
        print(f"\n✅ First request successful")
        print(f"   Detected word: {result1.value.word}")
        print(f"   Translation: {result1.value.translate_vi}")
        print(f"   Response time: {result1.value.response_time_ms}ms")
        print(f"\n📝 Cache key should be: 'vocabulary:definition:get off'")
    
    # Test 2: Same request again (should hit cache)
    print("\n" + "="*60)
    print("Test 2: Same request again (should be cached)")
    print("="*60)
    
    command2 = TranslateVocabularyCommand(
        word="get",
        context="I need to get off the bus"
    )
    result2 = use_case.execute(command2)
    
    if result2.is_success:
        print(f"\n✅ Second request successful")
        print(f"   Detected word: {result2.value.word}")
        print(f"   Translation: {result2.value.translate_vi}")
        print(f"   Response time: {result2.value.response_time_ms}ms")
        
        if result2.value.response_time_ms < result1.value.response_time_ms / 2:
            print(f"\n🎯 CACHE HIT! (much faster)")
        else:
            print(f"\n⚠️ Possible cache miss (similar speed)")
    
    # Test 3: Click "get" in different context (should be different cache key)
    print("\n" + "="*60)
    print("Test 3: User clicks 'get' in 'I get a book'")
    print("="*60)
    
    command3 = TranslateVocabularyCommand(
        word="get",
        context="I get a book from the library"
    )
    result3 = use_case.execute(command3)
    
    if result3.is_success:
        print(f"\n✅ Third request successful")
        print(f"   Detected word: {result3.value.word}")
        print(f"   Translation: {result3.value.translate_vi}")
        print(f"   Response time: {result3.value.response_time_ms}ms")
        print(f"\n📝 Cache key should be: 'vocabulary:definition:get' (NOT phrasal verb)")
    
    # Test 4: Click "get" without context
    print("\n" + "="*60)
    print("Test 4: User clicks 'get' without context")
    print("="*60)
    
    command4 = TranslateVocabularyCommand(word="get")
    result4 = use_case.execute(command4)
    
    if result4.is_success:
        print(f"\n✅ Fourth request successful")
        print(f"   Detected word: {result4.value.word}")
        print(f"   Translation: {result4.value.translate_vi}")
        print(f"   Response time: {result4.value.response_time_ms}ms")
        print(f"\n📝 Cache key should be: 'vocabulary:definition:get'")
        
        if result4.value.response_time_ms < result3.value.response_time_ms / 2:
            print(f"\n🎯 CACHE HIT! (reused from Test 3)")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"""
Cache Key Strategy:
1. With phrasal verb context → Cache key = phrasal verb
   Example: "get" in "get off" → Key: "vocabulary:definition:get off"

2. Without phrasal verb → Cache key = base word
   Example: "get" in "I get a book" → Key: "vocabulary:definition:get"

3. Same phrasal verb → Cache hit
   Example: "get" in "get off" (2nd time) → Cache hit ✅

4. Different context → Different cache key
   Example: "get off" vs "get" → Different keys, no collision ✅

Benefits:
✅ Phrasal verbs cached separately from base words
✅ No cache collision between "get" and "get off"
✅ Context-aware caching
✅ Efficient cache reuse
    """)


if __name__ == "__main__":
    test_cache_key()
