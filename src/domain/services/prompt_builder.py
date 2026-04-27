"""Prompt builder utilities for LLM interactions.

AWS Best Practices Applied:
- Spoken-first format: short, natural, conversational
- Persona-driven: character identity before rules
- Minimal constraints: guide don't over-constrain
- Natural speech elements per Nova Sonic guidelines

Reference: https://docs.aws.amazon.com/nova/latest/userguide/prompting-speech-best-practices.html
"""

from typing import Optional, Union


# Level-specific language guidance (CEFR-aligned, spoken-first)
_LEVEL_GUIDANCE = {
    "A1": "Use very simple words and short sentences. Speak slowly and clearly. Max 1-2 sentences.",
    "A2": "Use simple everyday vocabulary. Keep it short and friendly. Max 2 sentences.",
    "B1": "Use natural everyday language. 2-3 sentences. Ask one follow-up question.",
    "B2": "Use varied vocabulary and natural phrasing. 2-4 sentences.",
    "C1": "Use sophisticated, nuanced language. 3-5 sentences. Engage deeply.",
    "C2": "Speak naturally at native level. Fluid, natural conversation.",
}


def build_session_prompt(
    scenario_title: str,
    context: str,
    learner_role: str,
    ai_role: str,
    level: str,
    selected_goal: str,
    ai_character: str,
    prompt_version: str = "v2",
) -> str:
    """Build the snapshot prompt stored with the session for audit/replay."""
    goal_text = selected_goal.strip() if selected_goal else "practice natural conversation"
    level_guidance = _LEVEL_GUIDANCE.get(level, _LEVEL_GUIDANCE["B1"])

    return (
        f"[v{prompt_version}] scenario={scenario_title} level={level} "
        f"ai_role={ai_role} learner_role={learner_role} "
        f"character={ai_character} goal={goal_text}"
    )


class OptimizedPromptBuilder:
    """
    Build natural, spoken-first prompts for Amazon Nova conversation models.

    Follows AWS Nova Sonic best practices:
    - Short, natural responses (spoken transcript style)
    - Persona-first: establish character before rules
    - Emotional expression: "Haha", "Hmm", "Oh!" where appropriate
    - Natural speech markers: "Well,", "You know,", "Actually,"
    - No markdown formatting in responses (spoken output)

    Reference: https://docs.aws.amazon.com/nova/latest/userguide/prompting-speech-best-practices.html
    """

    @classmethod
    def build(
        cls,
        scenario_title: str,
        learner_role: str,
        ai_role: str,
        level: Union[str, object],
        selected_goal: Optional[str] = None,
        ai_character: str = "Sarah",
    ) -> str:
        """
        Build a natural, conversational system prompt.

        Args:
            scenario_title: Scenario name (e.g., "Restaurant", "Airport")
            learner_role: Learner's role in the scenario
            ai_role: AI's role in the scenario
            level: CEFR proficiency level (A1-C2)
            selected_goal: Learning goal for this session
            ai_character: Character name (Sarah, Marco, Emma, James)

        Returns:
            Natural system prompt string
        """
        level_str = level.value if hasattr(level, "value") else str(level)
        if level_str not in _LEVEL_GUIDANCE:
            level_str = "B1"

        level_guidance = _LEVEL_GUIDANCE[level_str]
        goal_text = selected_goal.strip() if selected_goal else "practice natural conversation"

        # Character personality mapping
        personality = cls._get_personality(ai_character, level_str)

        return f"""You are {ai_character}, a {ai_role} in a {scenario_title} scenario. {personality} You're having a real spoken conversation with a language learner playing {learner_role}.

Keep responses short and natural — {level_guidance}

Start each response with a tone cue: [warmly], [encouragingly], [thoughtfully], [gently], [enthusiastically], [playfully], [supportively], [calmly], [excitedly] — pick what fits the moment. Then use natural speech markers like "Well,", "Oh!", "Hmm," or "Actually," where they feel right.

Help the learner work toward: {goal_text}

When they make grammar mistakes, model the correct form naturally in your reply without pointing it out. If they write in Vietnamese, gently say "Please try in English! I'll help you." then give a simple English prompt. If they go off-topic, naturally steer back.

Examples:
[warmly] Oh, that sounds great! What did you enjoy most?
[encouragingly] Well done! So, what would you like to do next?
[thoughtfully] Hmm, interesting point. Have you considered...?"""

    @classmethod
    def _get_personality(cls, character: str, level: str) -> str:
        """Get character personality description."""
        personalities = {
            "Sarah": {
                "A1": "You are warm, patient, and encouraging. You speak slowly and clearly.",
                "A2": "You are friendly, supportive, and helpful. You keep things simple.",
                "B1": "You are engaging, curious, and natural. You enjoy good conversation.",
                "B2": "You are thoughtful and articulate. You enjoy exploring ideas.",
                "C1": "You are intellectually engaging and sophisticated.",
                "C2": "You speak naturally and fluently, like a native speaker.",
            },
            "Marco": {
                "A1": "You are cheerful, patient, and encouraging.",
                "A2": "You are friendly and easygoing.",
                "B1": "You are relaxed, natural, and conversational.",
                "B2": "You are confident and engaging.",
                "C1": "You are articulate and intellectually curious.",
                "C2": "You are fluent and expressive.",
            },
            "Emma": {
                "A1": "You are gentle, patient, and very encouraging.",
                "A2": "You are warm and supportive.",
                "B1": "You are natural and friendly.",
                "B2": "You are thoughtful and nuanced.",
                "C1": "You are sophisticated and perceptive.",
                "C2": "You are eloquent and naturally expressive.",
            },
            "James": {
                "A1": "You are calm, patient, and clear.",
                "A2": "You are friendly and straightforward.",
                "B1": "You are natural and easygoing.",
                "B2": "You are confident and engaging.",
                "C1": "You are articulate and intellectually sharp.",
                "C2": "You are fluent and naturally expressive.",
            },
        }
        char_map = personalities.get(character, personalities["Sarah"])
        return char_map.get(level, char_map.get("B1", "You are friendly and natural."))


def build_xml_prompt(
    instruction: str,
    examples: list[dict],
    output_format: str,
) -> str:
    """Build a structured prompt with XML tags for classification/extraction tasks."""
    prompt = f"<instruction>\n{instruction}\n</instruction>\n\n"

    if examples:
        prompt += "<examples>\n"
        for i, example in enumerate(examples, 1):
            prompt += f"<example_{i}>\n"
            if "input" in example:
                prompt += f"Input: {example['input']}\n"
            if "output" in example:
                prompt += f"Output:\n{example['output']}\n"
            prompt += f"</example_{i}>\n\n"
        prompt += "</examples>\n\n"

    prompt += f"<output_format>\n{output_format}\n</output_format>"
    return prompt


def escape_json_string(text: str) -> str:
    """Escape special characters for JSON string values."""
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
