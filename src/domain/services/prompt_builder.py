def build_system_prompt(
    scenario: str,
    my_character: str,
    ai_character: str,
    level: str
) -> str:
    """
    Build the final system prompt for Bedrock based on the roleplay scenario.

    Args:
        scenario:     The context/situation (e.g., "Ordering food in a restaurant")
        my_character: The user's role (e.g., "A customer")
        ai_character: The AI's persona (e.g., "A polite waiter")
        level:        CEFR level string (e.g., "B1")

    Returns:
        Fully rendered system prompt string ready to pass to Bedrock.
    """
    return (
        f"You are participating in an English roleplay conversation.\n"
        f"Scenario: {scenario}\n"
        f"Your Character: {ai_character}\n"
        f"User's Character: {my_character}\n\n"
        f"The user is practicing English at the {level} level. "
        f"You must adjust your vocabulary, idioms, and sentence complexity to match this {level} level.\n"
        f"Keep your responses concise, natural, and conversational (1-3 sentences max). "
        f"Always move the conversation forward or ask a follow-up question.\n"
        f"Do NOT correct the user's grammar during the conversation — evaluation happens after the session ends.\n"
        f"Stay in character at all times."
    )
