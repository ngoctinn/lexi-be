from enum import Enum

class Gender(Enum):
    """Giới tính cho việc chọn giọng đọc AI."""
    MALE = "male"
    FEMALE = "female"

class ProficiencyLevel(Enum):
    """Trình độ ngoại ngữ theo khung tham chiếu CEFR."""
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

class Role(Enum):
    """Phân quyền người dùng trong hệ thống."""
    LEARNER = "LEARNER"
    ADMIN = "ADMIN"

class Speaker(Enum):
    """Vai trò của người nói trong lượt hội thoại."""
    AI = "AI"
    USER = "USER"

class VocabType(Enum):
    """Loại từ vựng"""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    INTERJECTION = "interjection"
    PHRASE = "phrase"
    IDIOM = "idiom"

