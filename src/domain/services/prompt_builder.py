def build_session_prompt(
    scenario_title: str,
    context: str,
    learner_role: str,
    ai_role: str,
    level: str,
    selected_goals: list[str],
    ai_gender: str,
    prompt_version: str = "v1",
) -> str:
    """
    Build the snapshot prompt for a speaking session.

    Prompt snapshot is backend-owned so the session can be replayed and audited
    even if the frontend prompt template changes later.
    """
    goals_text = " | ".join(goal.strip() for goal in selected_goals if goal.strip())
    return (
        f"Prompt version: {prompt_version}\n"
        f"Scenario: {scenario_title}\n"
        f"Context: {context}\n"
        f"Learner role: {learner_role}\n"
        f"AI role: {ai_role}\n"
        f"AI gender: {ai_gender}\n"
        f"Level: {level}\n"
        f"Goals: {goals_text}\n\n"
        f"You are participating in an English roleplay conversation.\n"
        f"Keep your responses concise, natural, and conversational (1-3 sentences max).\n"
        f"Always move the conversation forward or ask a follow-up question.\n"
        f"Do NOT correct the user's grammar during the conversation — evaluation happens after the session ends.\n"
        f"Stay in character at all times."
    )


def build_system_prompt(
    scenario: str,
    my_character: str,
    ai_character: str,
    level: str,
) -> str:
    """Backward-compatible wrapper for older callers."""
    return build_session_prompt(
        scenario_title=scenario,
        context=scenario,
        learner_role=my_character,
        ai_role=ai_character,
        level=level,
        selected_goals=[],
        ai_gender="female",
    )
