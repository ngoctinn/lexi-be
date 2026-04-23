_LEVEL_INSTRUCTIONS = {
    "A1": "Use very simple words. Max 1-2 short sentences. Speak slowly and clearly.",
    "A2": "Use simple vocabulary. Max 2 sentences. Ask one simple question.",
    "B1": "Use everyday vocabulary. 2-3 sentences. Ask follow-up questions.",
    "B2": "Use varied vocabulary. 2-4 sentences. Discuss ideas naturally.",
    "C1": "Use sophisticated language. 3-5 sentences. Engage deeply.",
    "C2": "Use native-level language. Natural conversation flow.",
}


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
    level_instruction = _LEVEL_INSTRUCTIONS.get(level, _LEVEL_INSTRUCTIONS["B1"])
    first_goal = selected_goals[0] if selected_goals else "continue the conversation"

    return (
        f"Prompt version: {prompt_version}\n"
        f"Scenario: {scenario_title}\n"
        f"Context: {context}\n"
        f"Learner role: {learner_role}\n"
        f"AI role: {ai_role}\n"
        f"AI gender: {ai_gender}\n"
        f"Level: {level}\n"
        f"Goals: {goals_text}\n\n"
        f"You are playing the role of {ai_role} in a roleplay conversation.\n"
        f"LANGUAGE LEVEL: {level} — {level_instruction}\n\n"
        f"CONVERSATION RULES:\n"
        f"1. Stay in character as {ai_role} at all times.\n"
        f"2. Keep responses SHORT and NATURAL (match the level above).\n"
        f"3. Always move the conversation forward — ask a question or prompt the next action.\n"
        f"4. Do NOT correct grammar during conversation. Evaluation happens after.\n"
        f"5. If the learner goes off-topic, gently redirect: "
        f"\"That's interesting! But let's get back to {scenario_title}...\"\n"
        f"6. If the learner uses inappropriate language: "
        f"\"Let's keep it professional. Now, {first_goal}...\"\n"
        f"7. If the learner writes in Vietnamese, respond: "
        f"\"Please try in English! I'll help you. [simple English prompt]\"\n"
        f"8. NEVER say you are an AI unless directly asked."
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
