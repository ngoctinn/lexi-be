"""Adapter: Dictionary API → DictionaryService port."""

import json
import logging
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional
from dataclasses import asdict

import simplemma

from application.service_ports.dictionary_service import DictionaryService
from domain.entities.vocabulary import Vocabulary, Meaning, Phonetic
from domain.exceptions.dictionary_exceptions import (
    WordNotFoundError,
    DictionaryServiceError,
    DictionaryTimeoutError
)
from infrastructure.services.cache_service import CacheService
from infrastructure.services.retry_service import RetryService

logger = logging.getLogger(__name__)

DICTIONARY_API_BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en"
DICTIONARY_API_TIMEOUT = 30  # seconds

# Common particles for phrasal verb detection
PARTICLES = [
    "up", "down", "off", "on", "out", "in",
    "away", "back", "over", "through", "around",
    "along", "by", "into", "onto", "upon"
]


class HTTPErrorWithStatus(Exception):
    """Wrapper for HTTP errors that exposes status code to RetryService."""
    
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.response = {"status_code": status_code}


class DictionaryServiceAdapter(DictionaryService):
    """
    Adapter: Dictionary API → DictionaryService port.
    
    Implements DictionaryService by calling Dictionary API with:
    - 30-second timeout
    - Error handling for 404, 5xx, timeout
    - Logging for all API calls
    - Support for phrasal verbs (spaces, hyphens, apostrophes)
    - Context-aware phrasal verb detection with lemmatization
    - Two-tier caching (in-memory + DynamoDB) with 24-hour TTL
    """

    def __init__(
        self,
        cache_service: Optional[CacheService] = None,
        retry_service: Optional[RetryService] = None
    ):
        """
        Initialize DictionaryServiceAdapter.
        
        Args:
            cache_service: Optional CacheService for caching responses
            retry_service: Optional RetryService for retry logic
        """
        self._cache = cache_service
        self._retry = retry_service if retry_service else RetryService()

    def lemmatize_word(self, word: str) -> list[str]:
        """
        Lemmatize word using Simplemma.
        
        Args:
            word: Word to lemmatize
        
        Returns:
            List of candidates [original, lemma] (if different)
        """
        word_lower = word.lower()
        lemma = simplemma.lemmatize(word_lower, lang='en')
        
        # Return both original and lemma if different
        if lemma != word_lower:
            return [word_lower, lemma]
        return [word_lower]

    def _find_word_in_context(self, word: str, context: str) -> int:
        """
        Find word in context with flexible matching (base form or inflected form).
        
        Args:
            word: Word to find (could be base or inflected form)
            context: Full sentence
        
        Returns:
            Index of word in context, or -1 if not found
        """
        words = context.lower().split()
        word_lower = word.lower()
        
        # First try exact match
        try:
            return words.index(word_lower)
        except ValueError:
            pass
        
        # Try lemma matching: find a word in context whose lemma matches word's lemma
        word_lemmas = set(self.lemmatize_word(word))
        
        for idx, context_word in enumerate(words):
            context_lemmas = set(self.lemmatize_word(context_word))
            # If any lemma matches, we found it
            if word_lemmas & context_lemmas:
                return idx
        
        return -1

    def find_phrasal_verb_candidates(self, word: str, context: str) -> list[str]:
        """
        Find phrasal verb candidates with lemmatization and flexible word matching.
        
        Args:
            word: Word user clicked (could be verb OR particle, inflected OR base)
            context: Full sentence
        
        Returns:
            List of candidates to try (ordered by priority)
        """
        words = context.lower().split()
        
        # Find word in context with flexible matching (handles inflected forms)
        idx = self._find_word_in_context(word, context)
        
        if idx == -1:
            # Word not found in context, just lemmatize it
            return self.lemmatize_word(word)
        
        candidates = []
        
        # Get lemmas for clicked word
        word_lemmas = self.lemmatize_word(word)
        
        # Case 1: User clicked VERB → check next word for particle
        # Example: "got" in "I got off" → try ["got off", "get off"]
        if idx + 1 < len(words):
            next_word = words[idx + 1]
            if next_word in PARTICLES:
                for lemma in word_lemmas:
                    candidates.append(f"{lemma} {next_word}")
        
        # Case 2: User clicked PARTICLE → check previous word
        # Example: "off" in "I got off" → try ["got off", "get off"]
        if idx > 0 and word.lower() in PARTICLES:
            prev_word = words[idx - 1]
            prev_lemmas = self.lemmatize_word(prev_word)
            for lemma in prev_lemmas:
                candidates.append(f"{lemma} {word.lower()}")
        
        # Fallback: standalone word lemmas
        candidates.extend(word_lemmas)
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        
        return unique

    def get_word_definition(self, word: str, context: Optional[str] = None) -> Vocabulary:
        """
        Fetch word definition from Dictionary API with phrasal verb detection.
        
        Args:
            word: English word (any form: base, V2, V3, V-ed, V-ing)
            context: Optional sentence containing the word for phrasal verb detection
        
        Returns:
            Vocabulary entity with phonetic, meanings, and audio URL
        
        Raises:
            WordNotFoundError: Word not found in dictionary (HTTP 404)
            DictionaryServiceError: External service unavailable (HTTP 5xx)
            DictionaryTimeoutError: Request exceeded 30 seconds
        """
        # Generate candidates with lemmatization and phrasal verb detection
        if context:
            candidates = self.find_phrasal_verb_candidates(word, context)
        else:
            candidates = self.lemmatize_word(word)
        
        # Try each candidate in order
        last_error = None
        for candidate in candidates:
            try:
                logger.info(f"Trying candidate: {candidate}")
                return self._fetch_from_api(candidate)
            except WordNotFoundError as e:
                last_error = e
                continue  # Try next candidate
        
        # All candidates failed
        if last_error:
            raise last_error
        else:
            raise WordNotFoundError(f"Word '{word}' not found in dictionary")

    def _fetch_from_api(self, word: str) -> Vocabulary:
        """
        Fetch word definition from Dictionary API with caching and retry.
        
        Args:
            word: English word or phrasal verb
        
        Returns:
            Vocabulary entity
        
        Raises:
            WordNotFoundError: Word not found (HTTP 404)
            DictionaryServiceError: Service error (HTTP 5xx)
            DictionaryTimeoutError: Request timeout
        """
        word_clean = word.strip()
        cache_key = f"vocabulary:definition:{word_clean.lower()}"
        
        # Check cache first
        if self._cache:
            try:
                cached_data = self._cache.get(cache_key)
                if cached_data:
                    logger.info(f"Cache hit: {word_clean}")
                    return self._deserialize_vocabulary(cached_data)
            except Exception as e:
                logger.warning(f"Cache lookup failed for {word_clean}: {e}")
                # Continue without cache (graceful degradation)
        
        # Cache miss - fetch from API with retry
        if self._cache:
            logger.info(f"Cache miss: {word_clean}")
        
        # Wrap API call with retry logic
        def api_call():
            return self._make_api_request(word_clean)
        
        try:
            vocabulary = self._retry.execute_with_retry(
                func=api_call,
                max_retries=2,
                backoff_delays=[1, 2]
            )
        except HTTPErrorWithStatus as e:
            # Convert back to domain exceptions
            status_code = e.response["status_code"]
            if status_code == 404:
                raise WordNotFoundError(f"Word '{word_clean}' not found in dictionary")
            elif status_code >= 500:
                raise DictionaryServiceError(
                    f"Dictionary service temporarily unavailable (HTTP {status_code})"
                )
            else:
                raise DictionaryServiceError(f"Dictionary API error (HTTP {status_code})")
        
        # Cache successful response
        if self._cache:
            try:
                serialized = self._serialize_vocabulary(vocabulary)
                self._cache.set(cache_key, serialized, ttl_seconds=86400)  # 24 hours
                logger.debug(f"Cached definition: {word_clean}")
            except Exception as e:
                logger.warning(f"Cache storage failed for {word_clean}: {e}")
                # Continue without caching (graceful degradation)
        
        return vocabulary

    def _make_api_request(self, word: str) -> Vocabulary:
        """
        Make HTTP request to Dictionary API.
        
        Args:
            word: English word or phrasal verb
        
        Returns:
            Vocabulary entity
        
        Raises:
            HTTPErrorWithStatus: HTTP error with status code
            DictionaryTimeoutError: Request timeout
            DictionaryServiceError: Connection or other errors
        """
        start_time = time.time()
        
        try:
            # URL encode the word (handles spaces, hyphens, apostrophes)
            encoded_word = urllib.parse.quote(word)
            url = f"{DICTIONARY_API_BASE_URL}/{encoded_word}"
            
            logger.info(f"Fetching definition for word: {word}")
            
            # Make HTTP request with timeout
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0')
            
            response = urllib.request.urlopen(request, timeout=DICTIONARY_API_TIMEOUT)
            response_time = time.time() - start_time
            
            # Parse response
            data = json.loads(response.read().decode('utf-8'))
            
            logger.info(
                f"Dictionary API success: word={word}, "
                f"status=200, response_time={response_time:.3f}s"
            )
            
            return self._parse_response(data, word)
            
        except urllib.error.HTTPError as e:
            response_time = time.time() - start_time
            
            if e.code == 404:
                logger.warning(
                    f"Dictionary API 404: word={word}, "
                    f"response_time={response_time:.3f}s"
                )
            elif e.code == 429:
                logger.warning(
                    f"Dictionary API rate limit: word={word}, "
                    f"status=429, response_time={response_time:.3f}s"
                )
            elif e.code >= 500:
                logger.error(
                    f"Dictionary API server error: word={word}, "
                    f"status={e.code}, response_time={response_time:.3f}s"
                )
            else:
                logger.error(
                    f"Dictionary API error: word={word}, "
                    f"status={e.code}, response_time={response_time:.3f}s"
                )
            
            # Wrap in HTTPErrorWithStatus for RetryService
            raise HTTPErrorWithStatus(e.code, str(e))
        
        except urllib.error.URLError as e:
            response_time = time.time() - start_time
            
            # Check if it's a timeout
            if "timed out" in str(e.reason).lower() or "timeout" in str(e.reason).lower():
                logger.error(
                    f"Dictionary API timeout: word={word}, "
                    f"response_time={response_time:.3f}s"
                )
                raise DictionaryTimeoutError(
                    f"Dictionary API request timed out after {DICTIONARY_API_TIMEOUT}s"
                )
            
            logger.error(
                f"Dictionary API connection error: word={word}, "
                f"error={e.reason}, response_time={response_time:.3f}s"
            )
            raise DictionaryServiceError(f"Dictionary API connection error: {e.reason}")
        
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(
                f"Unexpected error fetching definition: word={word}, "
                f"error={type(e).__name__}: {e}, response_time={response_time:.3f}s"
            )
            raise DictionaryServiceError(f"Failed to fetch definition: {e}")

    def _parse_response(self, data: list, word: str) -> Vocabulary:
        """
        Parse Dictionary API response into Vocabulary entity.
        
        Args:
            data: List of word entries from Dictionary API
            word: Original word
        
        Returns:
            Vocabulary entity
        
        Raises:
            WordNotFoundError: If response is empty or invalid
        """
        if not data or not isinstance(data, list) or len(data) == 0:
            raise WordNotFoundError(f"Word '{word}' not found in dictionary")
        
        entry = data[0]
        
        # Extract word (use API's word, which may differ from input)
        api_word = entry.get("word", word)
        
        # Extract primary phonetic (top-level field)
        phonetic = entry.get("phonetic", "")
        
        # Extract audio URL (from first phonetic with audio)
        audio_url = None
        phonetics = entry.get("phonetics", [])
        for p in phonetics:
            if p.get("audio"):
                audio_url = p["audio"]
                break
        
        # Extract origin (if available)
        origin = entry.get("origin")
        
        # Extract meanings (ALL meanings from API)
        meanings = []
        api_meanings = entry.get("meanings", [])
        
        for meaning_data in api_meanings:
            part_of_speech = meaning_data.get("partOfSpeech", "")
            
            # Get FIRST definition only
            definitions = meaning_data.get("definitions", [])
            if not definitions:
                continue
            
            first_def = definitions[0]
            definition = first_def.get("definition", "")
            example = first_def.get("example", "")
            
            meanings.append(Meaning(
                part_of_speech=part_of_speech,
                definition=definition,
                definition_vi="",  # Translation will be added by use case
                example=example,
                example_vi=""  # Translation will be added by use case
            ))
        
        return Vocabulary(
            word=api_word,
            translate_vi="",  # Translation will be added by use case
            phonetic=phonetic,
            audio_url=audio_url,
            meanings=meanings,
            origin=origin
        )

    def _serialize_vocabulary(self, vocab: Vocabulary) -> dict:
        """
        Serialize Vocabulary entity to dict for caching.
        
        Args:
            vocab: Vocabulary entity
        
        Returns:
            Dict representation
        """
        return {
            "word": vocab.word,
            "translate_vi": vocab.translate_vi,
            "phonetic": vocab.phonetic,
            "audio_url": vocab.audio_url,
            "origin": vocab.origin,
            "meanings": [
                {
                    "part_of_speech": m.part_of_speech,
                    "definition": m.definition,
                    "definition_vi": m.definition_vi,
                    "example": m.example,
                    "example_vi": m.example_vi
                }
                for m in vocab.meanings
            ]
        }

    def _deserialize_vocabulary(self, data: dict) -> Vocabulary:
        """
        Deserialize dict from cache to Vocabulary entity.
        
        Args:
            data: Dict representation
        
        Returns:
            Vocabulary entity
        """
        meanings = [
            Meaning(
                part_of_speech=m["part_of_speech"],
                definition=m["definition"],
                definition_vi=m.get("definition_vi", ""),
                example=m.get("example", ""),
                example_vi=m.get("example_vi", "")
            )
            for m in data.get("meanings", [])
        ]
        
        return Vocabulary(
            word=data["word"],
            translate_vi=data.get("translate_vi", ""),
            phonetic=data.get("phonetic", ""),
            audio_url=data.get("audio_url"),
            meanings=meanings,
            origin=data.get("origin")
        )
