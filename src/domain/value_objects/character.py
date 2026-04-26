"""Character configuration for AI conversation partners."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Character:
    """AI character with voice mapping."""
    name: str          # Sarah, Marco, Emma, James
    polly_voice: str   # Joanna, Matthew, Amy, Brian
    gender: str        # female, male
    accent: str        # US, British


# 4 Characters with Polly voice mapping
CHARACTERS = {
    "Sarah": Character(
        name="Sarah",
        polly_voice="Joanna",
        gender="female",
        accent="US",
    ),
    "Marco": Character(
        name="Marco",
        polly_voice="Matthew",
        gender="male",
        accent="US",
    ),
    "Emma": Character(
        name="Emma",
        polly_voice="Amy",
        gender="female",
        accent="British",
    ),
    "James": Character(
        name="James",
        polly_voice="Brian",
        gender="male",
        accent="British",
    ),
}


def get_character(name: str) -> Character:
    """Get character by name.
    
    Args:
        name: Character name (Sarah, Marco, Emma, James)
        
    Returns:
        Character object
        
    Raises:
        ValueError: If character not found
    """
    if name not in CHARACTERS:
        raise ValueError(f"Character '{name}' not found. Available: {list(CHARACTERS.keys())}")
    return CHARACTERS[name]


def list_characters() -> list[str]:
    """List all available character names."""
    return list(CHARACTERS.keys())
