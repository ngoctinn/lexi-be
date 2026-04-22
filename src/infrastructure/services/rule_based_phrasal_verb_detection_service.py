import re
from dataclasses import dataclass

from application.services.phrasal_verb_detection_service import (
    AnalyzedVocabularyToken,
    PhrasalVerbDetectionService,
)


_PHRASAL_VERBS: set[str] = {
    "ask for",
    "break down",
    "bring up",
    "call back",
    "call off",
    "carry on",
    "check in",
    "check out",
    "come back",
    "come in",
    "come up",
    "fill out",
    "find out",
    "figure out",
    "get up",
    "give up",
    "go on",
    "hand in",
    "hold on",
    "look for",
    "look up",
    "make up",
    "pick up",
    "put off",
    "put on",
    "run out",
    "set up",
    "show up",
    "take off",
    "turn off",
    "turn on",
    "wake up",
    "work out",
}

_IRREGULAR_VERB_LEMMAS: dict[str, str] = {
    "took": "take",
    "taken": "take",
    "gave": "give",
    "given": "give",
    "went": "go",
    "gone": "go",
    "came": "come",
    "found": "find",
    "brought": "bring",
    "ran": "run",
    "set": "set",
    "made": "make",
    "woke": "wake",
    "woken": "wake",
    "held": "hold",
    "put": "put",
    "shown": "show",
    "showed": "show",
}

_WORD_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|[^\w\s]")
_MAX_SEPARATED_GAP = 4


@dataclass(frozen=True)
class _WordToken:
    text: str
    lower: str
    is_alpha: bool


class RuleBasedPhrasalVerbDetectionService(PhrasalVerbDetectionService):
    def __init__(self):
        self._phrases_by_verb: dict[str, list[tuple[str, str]]] = {}
        for base in _PHRASAL_VERBS:
            verb, particle = base.split(" ", 1)
            self._phrases_by_verb.setdefault(verb, []).append((base, particle))

    def analyze(self, text: str) -> list[AnalyzedVocabularyToken]:
        tokens = self._tokenize(text)
        results: list[AnalyzedVocabularyToken] = []
        index = 0

        while index < len(tokens):
            token = tokens[index]
            if not token.is_alpha:
                results.append(AnalyzedVocabularyToken(text=token.text, token_type="word"))
                index += 1
                continue

            matched = self._match_phrase(tokens, index)
            if matched:
                end_index, base = matched
                phrase_text = " ".join(part.text for part in tokens[index : end_index + 1])
                results.append(
                    AnalyzedVocabularyToken(
                        text=phrase_text,
                        token_type="phrase",
                        base=base,
                    )
                )
                index = end_index + 1
                continue

            results.append(AnalyzedVocabularyToken(text=token.text, token_type="word"))
            index += 1

        return results

    def _tokenize(self, text: str) -> list[_WordToken]:
        parts = _WORD_PATTERN.findall(text)
        return [
            _WordToken(
                text=part,
                lower=part.lower(),
                is_alpha=bool(re.fullmatch(r"[A-Za-z]+(?:'[A-Za-z]+)?", part)),
            )
            for part in parts
        ]

    def _match_phrase(self, tokens: list[_WordToken], start_index: int) -> tuple[int, str] | None:
        token = tokens[start_index]
        lemmas = self._candidate_lemmas(token.lower)
        best: tuple[int, str] | None = None

        for lemma in lemmas:
            candidates = self._phrases_by_verb.get(lemma, [])
            for base, particle in candidates:
                contiguous_index = start_index + 1
                if (
                    contiguous_index < len(tokens)
                    and tokens[contiguous_index].is_alpha
                    and tokens[contiguous_index].lower == particle
                ):
                    best = self._pick_longer(best, (contiguous_index, base))

                separated_end = min(len(tokens), start_index + _MAX_SEPARATED_GAP + 2)
                for particle_index in range(start_index + 2, separated_end):
                    current = tokens[particle_index]
                    if not current.is_alpha:
                        break
                    if current.lower != particle:
                        continue
                    if any(not middle.is_alpha for middle in tokens[start_index + 1 : particle_index]):
                        continue
                    best = self._pick_longer(best, (particle_index, base))
                    break

        return best

    def _candidate_lemmas(self, word: str) -> list[str]:
        lemmas: set[str] = {word}
        irregular = _IRREGULAR_VERB_LEMMAS.get(word)
        if irregular:
            lemmas.add(irregular)

        if word.endswith("ies") and len(word) > 3:
            lemmas.add(word[:-3] + "y")

        if word.endswith("ing") and len(word) > 4:
            stem = word[:-3]
            lemmas.add(stem)
            lemmas.add(stem + "e")
            if len(stem) > 2 and stem[-1] == stem[-2]:
                lemmas.add(stem[:-1])

        if word.endswith("ed") and len(word) > 3:
            stem = word[:-2]
            lemmas.add(stem)
            lemmas.add(stem + "e")
            if len(stem) > 2 and stem[-1] == stem[-2]:
                lemmas.add(stem[:-1])

        if word.endswith("es") and len(word) > 3:
            lemmas.add(word[:-2])

        if word.endswith("s") and len(word) > 2:
            lemmas.add(word[:-1])

        filtered = [lemma for lemma in lemmas if lemma in self._phrases_by_verb]
        return sorted(filtered, key=len, reverse=True)

    def _pick_longer(
        self,
        current: tuple[int, str] | None,
        candidate: tuple[int, str],
    ) -> tuple[int, str]:
        if current is None:
            return candidate
        if candidate[0] > current[0]:
            return candidate
        return current
