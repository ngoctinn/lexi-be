#!/usr/bin/env python3
"""Test MyMemory API with detailed vocabulary translation."""

import requests
import json
import time

def translate_with_mymemory(text, source="en", target="vi"):
    """Translate text using MyMemory API."""
    url = "https://api.mymemory.translated.net/get"
    
    try:
        response = requests.get(url, params={
            "q": text,
            "langpair": f"{source}|{target}"
        }, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("responseData", {}).get("translatedText", text)
        else:
            return text
    except Exception as e:
        print(f"Error translating '{text}': {e}")
        return text


def test_vocabulary_translation():
    """Test translating a complete vocabulary entry."""
    print("\n" + "="*60)
    print("TEST: Complete Vocabulary Translation with MyMemory")
    print("="*60)
    
    # Simulate vocabulary data from Dictionary API
    vocabulary = {
        "word": "run",
        "meanings": [
            {
                "part_of_speech": "verb",
                "definition": "To move at a speed faster than a walk",
                "example": "She runs five miles every day"
            },
            {
                "part_of_speech": "noun",
                "definition": "An act of running",
                "example": "I went for a run this morning"
            },
            {
                "part_of_speech": "verb",
                "definition": "To operate or function",
                "example": "The engine runs smoothly"
            }
        ]
    }
    
    print(f"\n📚 Original vocabulary: {vocabulary['word']}")
    print(f"Meanings count: {len(vocabulary['meanings'])}")
    
    # Collect items to translate
    items_to_translate = [vocabulary["word"]]
    
    for meaning in vocabulary["meanings"]:
        items_to_translate.append(meaning["definition"])
        if meaning["example"]:
            items_to_translate.append(meaning["example"])
    
    print(f"\n📝 Items to translate: {len(items_to_translate)}")
    
    # Translate all items
    print(f"\n🔄 Translating...")
    start_time = time.time()
    
    translations = []
    for i, text in enumerate(items_to_translate):
        print(f"  [{i+1}/{len(items_to_translate)}] Translating: {text[:50]}...")
        translation = translate_with_mymemory(text)
        translations.append(translation)
        time.sleep(0.2)  # Rate limiting
    
    elapsed = int((time.time() - start_time) * 1000)
    
    print(f"\n✅ Translation completed in {elapsed}ms")
    print(f"Average per item: {elapsed // len(items_to_translate)}ms")
    
    # Display results
    print(f"\n" + "="*60)
    print("TRANSLATION RESULTS")
    print("="*60)
    
    print(f"\nWord: {vocabulary['word']}")
    print(f"Translation: {translations[0]}")
    
    translation_index = 1
    for i, meaning in enumerate(vocabulary["meanings"]):
        print(f"\n--- Meaning {i+1} ({meaning['part_of_speech']}) ---")
        print(f"Definition (EN): {meaning['definition']}")
        print(f"Definition (VI): {translations[translation_index]}")
        translation_index += 1
        
        if meaning["example"]:
            print(f"Example (EN): {meaning['example']}")
            print(f"Example (VI): {translations[translation_index]}")
            translation_index += 1
    
    # Compare with AWS Translate approach
    print(f"\n" + "="*60)
    print("COMPARISON")
    print("="*60)
    
    print(f"""
MyMemory API:
  - Total time: {elapsed}ms
  - Items translated: {len(items_to_translate)}
  - API calls: {len(items_to_translate)}
  - Cost: FREE (1000 words/day limit)
  - Quality: Good for common words
  
AWS Translate (Current):
  - Total time: ~1200ms (with batch translation issue)
  - Items translated: {len(items_to_translate)}
  - API calls: 7 (or 1 with batch)
  - Cost: $15 per million characters
  - Quality: Excellent
  
Recommendation:
  - Use MyMemory for common words (cache miss)
  - Fallback to AWS Translate for uncommon/technical words
  - Cache all translations in DynamoDB
    """)


def test_rate_limits():
    """Test MyMemory API rate limits."""
    print("\n" + "="*60)
    print("TEST: MyMemory API Rate Limits")
    print("="*60)
    
    words = ["hello", "world", "test", "example", "run", "walk", "jump", "swim", "eat", "drink"]
    
    print(f"\n📤 Testing {len(words)} rapid requests...")
    
    start = time.time()
    success_count = 0
    
    for word in words:
        try:
            response = requests.get("https://api.mymemory.translated.net/get", params={
                "q": word,
                "langpair": "en|vi"
            }, timeout=5)
            
            if response.status_code == 200:
                success_count += 1
            else:
                print(f"  ⚠️ Failed for '{word}': {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error for '{word}': {e}")
    
    elapsed = int((time.time() - start) * 1000)
    
    print(f"\n✅ Results:")
    print(f"  - Success: {success_count}/{len(words)}")
    print(f"  - Total time: {elapsed}ms")
    print(f"  - Average: {elapsed // len(words)}ms per request")
    
    if success_count == len(words):
        print(f"\n✅ No rate limiting detected for {len(words)} requests")
    else:
        print(f"\n⚠️ Some requests failed - may be rate limited")


if __name__ == "__main__":
    test_vocabulary_translation()
    test_rate_limits()
