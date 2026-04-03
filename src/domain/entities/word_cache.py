from dataclasses import dataclass

@dataclass
class WordCache:
    word: str
    word_type: str         # adjective, noun, verb, adverb, ...
    definition_vi: str     # Vietnamese definition
    phonetic: str          # IPA e.g. /ˈskeɪləbl/
    audio_s3_key: str      # Copied from WordCache — independent of cache TTL
    example_sentence: str
    source_api: str # Optional

