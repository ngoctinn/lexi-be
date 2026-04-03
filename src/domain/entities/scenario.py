from dataclasses import dataclass


@dataclass
class Scenario:
    """
    Represents a predefined ROLEPLAY SCENARIO curated by Admins.
    PK = SYSTEM#SCENARIOS  |  SK = SCENARIO#<ulid>
    
    This acts as a catalog of available situations users can choose to practice.
    """
    scenario_title: str             # Display title (e.g., "Job interview for a Frontend role")
    description: str       # Brief explanation of the scenario
    scenario_prompt: str          # The actual context prompt
    my_character: str      # E.g., "A nervous candidate"
    ai_character: str      # E.g., "A strict Technical Manager"
    ai_gender: str         # "male" | "female"
    recommended_level: str # E.g., "B1-C1" (Just a recommendation, user still selects their actual level in the Session)
    is_active: bool = True # Admin can toggle visibility on the app
    usage_count: int = 0   # Track popularity
