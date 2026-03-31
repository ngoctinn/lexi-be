from dataclasses import dataclass, field

@dataclass
class FlashCard:
    card_id: str
    user_id: str
    word: str
    definition: str
    
