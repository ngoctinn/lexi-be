import re
from dataclasses import dataclass

from application.services.phrasal_verb_detection_service import (
    AnalyzedVocabularyToken,
    PhrasalVerbDetectionService,
)


_PHRASE_DEFINITIONS_VI: dict[str, str] = {
    "ask for": "yêu cầu; xin",
    "break down": "hỏng; suy sụp",
    "bring up": "đề cập; nuôi dạy",
    "call back": "gọi lại",
    "call off": "hủy bỏ",
    "carry on": "tiếp tục",
    "check in": "làm thủ tục vào",
    "check out": "trả phòng; kiểm tra",
    "come back": "quay lại",
    "come in": "đi vào",
    "come up": "xảy ra; xuất hiện",
    "fill out": "điền (biểu mẫu)",
    "find out": "tìm ra",
    "figure out": "hiểu ra; tìm cách giải quyết",
    "get up": "thức dậy",
    "give up": "từ bỏ",
    "go on": "tiếp diễn",
    "hand in": "nộp",
    "hold on": "chờ một chút",
    "look for": "tìm kiếm",
    "look up": "tra cứu",
    "make up": "bịa ra; làm lành",
    "pick up": "nhặt lên; đón",
    "put off": "hoãn lại",
    "put on": "mặc vào",
    "run out": "hết",
    "set up": "thiết lập",
    "show up": "xuất hiện",
    "take off": "cởi ra; cất cánh",
    "turn off": "tắt",
    "turn on": "bật",
    "wake up": "thức dậy",
    "work out": "tìm ra; tập luyện",
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
        self._phrases_by_verb: dict[str, list[tuple[str, str, str]]] = {}
        for base, definition in _PHRASE_DEFINITIONS_VI.items():
            verb, particle = base.split(" ", 1)
            self._phrases_by_verb.setdefault(verb, []).append((base, particle, definition))

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
                end_index, base, definition = matched
                phrase_text = " ".join(part.text for part in tokens[index : end_index + 1])
                results.append(
                    AnalyzedVocabularyToken(
                        text=phrase_text,
                        token_type="phrase",
                        base=base,
                        definition_vi=definition,
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

    def _match_phrase(self, tokens: list[_WordToken], start_index: int) -> tuple[int, str, str] | None:
        token = tokens[start_index]
        lemmas = self._candidate_lemmas(token.lower)
        best: tuple[int, str, str] | None = None

        for lemma in lemmas:
            candidates = self._phrases_by_verb.get(lemma, [])
            for base, particle, definition in candidates:
                contiguous_index = start_index + 1
                if (
                    contiguous_index < len(tokens)
                    and tokens[contiguous_index].is_alpha
                    and tokens[contiguous_index].lower == particle
                ):
                    best = self._pick_longer(best, (contiguous_index, base, definition))

                separated_end = min(len(tokens), start_index + _MAX_SEPARATED_GAP + 2)
                for particle_index in range(start_index + 2, separated_end):
                    current = tokens[particle_index]
                    if not current.is_alpha:
                        break
                    if current.lower != particle:
                        continue
                    if any(not middle.is_alpha for middle in tokens[start_index + 1 : particle_index]):
                        continue
                    best = self._pick_longer(best, (particle_index, base, definition))
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
        current: tuple[int, str, str] | None,
        candidate: tuple[int, str, str],
    ) -> tuple[int, str, str]:
        if current is None:
            return candidate
        if candidate[0] > current[0]:
            return candidate
        return current
