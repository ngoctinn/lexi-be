from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from application.dtos.vocabulary.analyze.analyze_sentence_command import AnalyzeSentenceCommand
from application.use_cases.vocabulary.analyze_sentence import AnalyzeSentenceUC
from infrastructure.services.rule_based_phrasal_verb_detection_service import (
    RuleBasedPhrasalVerbDetectionService,
)


def test_detects_inflected_phrasal_verbs_and_keeps_original_phrase_text():
    service = RuleBasedPhrasalVerbDetectionService()

    items = service.analyze("I took off my jacket and am looking for my phone")

    simple_items = [
        {"text": item.text, "type": item.token_type, "base": item.base}
        for item in items
    ]

    assert simple_items == [
        {"text": "I", "type": "word", "base": None},
        {"text": "took off", "type": "phrase", "base": "take off"},
        {"text": "my", "type": "word", "base": None},
        {"text": "jacket", "type": "word", "base": None},
        {"text": "and", "type": "word", "base": None},
        {"text": "am", "type": "word", "base": None},
        {"text": "looking for", "type": "phrase", "base": "look for"},
        {"text": "my", "type": "word", "base": None},
        {"text": "phone", "type": "word", "base": None},
    ]


def test_detects_separated_phrasal_verb_within_limited_gap():
    service = RuleBasedPhrasalVerbDetectionService()

    items = service.analyze("Please turn the light off now")

    assert items[0].text == "Please"
    assert items[1].token_type == "phrase"
    assert items[1].text == "turn the light off"
    assert items[1].base == "turn off"
    assert items[2].text == "now"


def test_use_case_returns_response_payload_for_frontend_contract():
    service = RuleBasedPhrasalVerbDetectionService()
    use_case = AnalyzeSentenceUC(service)

    result = use_case.execute(
        AnalyzeSentenceCommand(text="They have taken off already")
    )

    assert result.is_success
    assert result.value is not None
    assert result.value.items[2].text == "taken off"
    assert result.value.items[2].type == "phrase"
    assert result.value.items[2].base == "take off"
