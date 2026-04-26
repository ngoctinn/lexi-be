#!/usr/bin/env python3
"""Test Vietnamese dictionary APIs."""

import requests
import json
import time

def test_free_dictionary_api():
    """Test FreeDictionaryAPI.com with translations."""
    print("\n" + "="*60)
    print("TEST 1: FreeDictionaryAPI.com")
    print("="*60)
    
    word = "run"
    url = f"https://api.freedictionaryapi.com/en/{word}"
    
    try:
        print(f"\n📤 Testing word: '{word}'")
        print(f"URL: {url}")
        
        start = time.time()
        response = requests.get(url, params={"translations": "true"}, timeout=10)
        elapsed = int((time.time() - start) * 1000)
        
        print(f"Status: {response.status_code}")
        print(f"Response time: {elapsed}ms")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"Response structure:")
            print(json.dumps(data, indent=2)[:1000])
            
            # Check for Vietnamese translations
            if "entries" in data:
                for entry in data["entries"]:
                    if "senses" in entry:
                        for sense in entry["senses"]:
                            if "translations" in sense:
                                print(f"\n📝 Found translations:")
                                for trans in sense["translations"][:3]:
                                    lang = trans.get("language", {})
                                    print(f"  - {lang.get('name', 'Unknown')}: {trans.get('word', 'N/A')}")
                                return True
            
            print("\n⚠️ No Vietnamese translations found")
            return False
        else:
            print(f"\n❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mymemory_api():
    """Test MyMemory Translation API (free tier)."""
    print("\n" + "="*60)
    print("TEST 2: MyMemory Translation API")
    print("="*60)
    
    word = "run"
    url = "https://api.mymemory.translated.net/get"
    
    try:
        print(f"\n📤 Testing word: '{word}'")
        print(f"URL: {url}")
        
        start = time.time()
        response = requests.get(url, params={
            "q": word,
            "langpair": "en|vi"
        }, timeout=10)
        elapsed = int((time.time() - start) * 1000)
        
        print(f"Status: {response.status_code}")
        print(f"Response time: {elapsed}ms")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"Translation: {data.get('responseData', {}).get('translatedText', 'N/A')}")
            print(f"Match: {data.get('responseData', {}).get('match', 'N/A')}")
            
            # Show matches
            if "matches" in data:
                print(f"\n📝 Alternative translations:")
                for match in data["matches"][:3]:
                    print(f"  - {match.get('translation', 'N/A')} (quality: {match.get('quality', 'N/A')})")
            
            return True
        else:
            print(f"\n❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_linguee_scraping():
    """Test Linguee (scraping approach - for reference only)."""
    print("\n" + "="*60)
    print("TEST 3: Linguee (Web Scraping)")
    print("="*60)
    
    word = "run"
    url = f"https://www.linguee.com/english-vietnamese/search?source=auto&query={word}"
    
    try:
        print(f"\n📤 Testing word: '{word}'")
        print(f"URL: {url}")
        
        start = time.time()
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }, timeout=10)
        elapsed = int((time.time() - start) * 1000)
        
        print(f"Status: {response.status_code}")
        print(f"Response time: {elapsed}ms")
        
        if response.status_code == 200:
            print(f"\n✅ Page loaded successfully!")
            print(f"Content length: {len(response.text)} bytes")
            print(f"\n⚠️ Note: Requires HTML parsing (BeautifulSoup) to extract translations")
            print(f"⚠️ Not recommended: Scraping is fragile and may violate ToS")
            return True
        else:
            print(f"\n❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_libre_translate():
    """Test LibreTranslate (open source, self-hostable)."""
    print("\n" + "="*60)
    print("TEST 4: LibreTranslate (Public Instance)")
    print("="*60)
    
    word = "run"
    url = "https://libretranslate.com/translate"
    
    try:
        print(f"\n📤 Testing word: '{word}'")
        print(f"URL: {url}")
        
        start = time.time()
        response = requests.post(url, json={
            "q": word,
            "source": "en",
            "target": "vi",
            "format": "text"
        }, timeout=10)
        elapsed = int((time.time() - start) * 1000)
        
        print(f"Status: {response.status_code}")
        print(f"Response time: {elapsed}ms")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"Translation: {data.get('translatedText', 'N/A')}")
            return True
        else:
            print(f"\n❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("VIETNAMESE DICTIONARY API TESTS")
    print("="*60)
    
    results = {
        "FreeDictionaryAPI": test_free_dictionary_api(),
        "MyMemory": test_mymemory_api(),
        "Linguee": test_linguee_scraping(),
        "LibreTranslate": test_libre_translate(),
    }
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    print("""
1. MyMemory API (RECOMMENDED)
   - Free tier: 1000 words/day
   - Fast response (~200-300ms)
   - Good quality translations
   - Simple REST API
   
2. LibreTranslate (ALTERNATIVE)
   - Open source, self-hostable
   - Free public instance (rate limited)
   - Can deploy own instance for unlimited usage
   
3. AWS Translate (CURRENT)
   - Keep as fallback
   - Use for uncommon words not in cache
    """)


if __name__ == "__main__":
    main()
