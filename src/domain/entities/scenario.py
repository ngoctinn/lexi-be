from dataclasses import dataclass

@dataclass
class Scenario:
    """
    Represents a predefined ROLEPLAY SCENARIO curated by Admins.
    PK = SYSTEM#SCENARIOS  |  SK = SCENARIO#<ulid>
    
    This acts as a catalog of available situations users can choose to practice.
    """
    session_id: int        
    scenario_title: str             # Display title (e.g., "Job interview for a Frontend role")
    scenario_prompt: str          # The actual context prompt
    my_character: str      # E.g., "A nervous candidate"
    ai_character: str      # E.g., "A strict Technical Manager"
    is_active: bool = True # Admin can toggle visibility on the app
    usage_count: int = 0   # Track popularity to show on top list recommendations
