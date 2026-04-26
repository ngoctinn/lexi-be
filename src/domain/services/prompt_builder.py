"""Prompt builder utilities for LLM interactions.

Provides reusable functions to build structured prompts with XML tags,
ensuring consistent formatting and reducing prompt engineering errors.
"""


# Level-specific instructions per CEFR level
_LEVEL_INSTRUCTIONS = {
    "A1": "Use very simple words. Max 1-2 short sentences. Speak slowly and clearly.",
    "A2": "Use simple vocabulary. Max 2 sentences. Ask one simple question.",
    "B1": "Use everyday vocabulary. 2-3 sentences. Ask follow-up questions.",
    "B2": "Use varied vocabulary. 2-4 sentences. Discuss ideas naturally.",
    "C1": "Use sophisticated language. 3-5 sentences. Engage deeply.",
    "C2": "Use native-level language. Natural conversation flow.",
}

# Implicit error correction instructions per CEFR level
_IMPLICIT_CORRECTION_INSTRUCTIONS = {
    "A1": "When learner makes grammar, vocabulary, or pronunciation mistakes, model correct usage naturally in your response without explicit correction. Continue conversation naturally while demonstrating proper forms. Maintain existing explicit correction rules for Vietnamese usage, inappropriate language, and off-topic responses.",
    "A2": "When learner makes grammar, vocabulary, or pronunciation mistakes, naturally model correct forms in your response without explicit correction statements. Continue conversation flow while demonstrating proper usage. Maintain existing explicit correction rules for Vietnamese usage, inappropriate language, and off-topic responses.",
    "B1": "When learner makes grammar, vocabulary, or pronunciation mistakes, incorporate correct usage naturally in your response without explicit correction. Continue conversation naturally while modeling proper forms. Maintain existing explicit correction rules for Vietnamese usage, inappropriate language, and off-topic responses.",
    "B2": "When learner makes grammar, vocabulary, or pronunciation mistakes, demonstrate correct usage naturally in your response without explicit correction statements. Continue conversation flow while modeling proper forms. Maintain existing explicit correction rules for Vietnamese usage, inappropriate language, and off-topic responses.",
    "C1": "When learner makes grammar, vocabulary, or pronunciation mistakes, model correct usage naturally in your response without explicit correction. Continue conversation naturally while demonstrating sophisticated proper forms. Maintain existing explicit correction rules for Vietnamese usage, inappropriate language, and off-topic responses.",
    "C2": "When learner makes grammar, vocabulary, or pronunciation mistakes, incorporate correct usage naturally in your response without explicit correction statements. Continue conversation flow while modeling native-level proper forms. Maintain existing explicit correction rules for Vietnamese usage, inappropriate language, and off-topic responses.",
}

# Few-shot examples demonstrating implicit error correction per CEFR level
_IMPLICIT_CORRECTION_EXAMPLES = {
    "A1": """
Example 1 (Grammar - Simple Present/Past):
Learner: "I go beach yesterday"
Good: "[warmly] When you went to the beach, did you swim?"
Bad: "You should say 'went', not 'go'."

Example 2 (Vocabulary - Simple Words):
Learner: "I eat food at place"
Good: "[warmly] You ate at a restaurant? What did you have?"
Bad: "The correct word is 'restaurant', not 'place'."

Example 3 (Pronunciation-Related):
Learner: "I like play football"
Good: "[warmly] You like playing football? That's great! Do you play often?"
Bad: "You need to say 'playing', not 'play'."
""",
    "A2": """
Example 1 (Tense Error):
Learner: "I am go to school every day"
Good: "[warmly] You go to school every day? What's your favorite subject?"
Bad: "You should say 'I go', not 'I am go'."

Example 2 (Vocabulary Error):
Learner: "I want buy new phone"
Good: "[warmly] You want to buy a new phone? What kind are you looking for?"
Bad: "You need 'to' before 'buy'."

Example 3 (Sentence Structure Error):
Learner: "Yesterday I go shopping and buy shoes"
Good: "[warmly] You went shopping yesterday and bought shoes? What color are they?"
Bad: "You should use past tense: 'went' and 'bought'."
""",
    "B1": """
Example 1 (Present Perfect Error):
Learner: "I have went to Paris last year"
Good: "[encouragingly] You went to Paris last year? That's wonderful! What did you enjoy most?"
Bad: "The correct form is 'I went', not 'I have went'."

Example 2 (Preposition Error):
Learner: "I'm interested for learning English"
Good: "[encouragingly] You're interested in learning English? What motivates you?"
Bad: "Use 'interested in', not 'interested for'."

Example 3 (Intermediate Vocabulary Error):
Learner: "The movie was very boring for me"
Good: "[naturally] The movie bored you? What kind of movies do you usually enjoy?"
Bad: "You should say 'bored me', not 'boring for me'."
""",
    "B2": """
Example 1 (Conditional Error):
Learner: "If I would have more time, I will travel more"
Good: "[thoughtfully] If you had more time, you'd travel more? Where would you go first?"
Bad: "The correct form is 'If I had', not 'If I would have'."

Example 2 (Passive Voice Error):
Learner: "The problem was happened last week"
Good: "[naturally] The problem happened last week? How was it resolved?"
Bad: "Don't use passive with 'happen'. Say 'happened'."

Example 3 (Advanced Vocabulary Error):
Learner: "The government should make laws more strict"
Good: "[thoughtfully] You think the government should make laws stricter? What specific areas concern you?"
Bad: "Say 'stricter', not 'more strict'."
""",
    "C1": """
Example 1 (Subjunctive Error):
Learner: "I suggest that he goes to the meeting"
Good: "[thoughtfully] You suggest that he go to the meeting? What makes you think he should attend?"
Bad: "Use subjunctive: 'he go', not 'he goes'."

Example 2 (Idiomatic Usage Error):
Learner: "He made a decision very quickly without thinking"
Good: "[naturally] He made a snap decision? What were the consequences?"
Bad: "Say 'snap decision', not 'decision very quickly'."

Example 3 (Sophisticated Vocabulary Error):
Learner: "The company's decision was very controversial between employees"
Good: "[thoughtfully] The company's decision was controversial among employees? What were the main points of contention?"
Bad: "Use 'among', not 'between' for more than two."
""",
}


def build_session_prompt(
    scenario_title: str,
    context: str,
    learner_role: str,
    ai_role: str,
    level: str,
    selected_goal: str,
    ai_character: str,
    prompt_version: str = "v1",
) -> str:
    """Build the snapshot prompt for a speaking session.

    Prompt snapshot is backend-owned so the session can be replayed and audited
    even if the frontend prompt template changes later.
    """
    goal_text = selected_goal.strip() if selected_goal else "general conversation"
    level_instruction = _LEVEL_INSTRUCTIONS.get(level, _LEVEL_INSTRUCTIONS["B1"])
    implicit_correction_instruction = _IMPLICIT_CORRECTION_INSTRUCTIONS.get(
        level, _IMPLICIT_CORRECTION_INSTRUCTIONS["B1"]
    )
    implicit_correction_examples = _IMPLICIT_CORRECTION_EXAMPLES.get(
        level, _IMPLICIT_CORRECTION_EXAMPLES.get("B1", "")
    )

    return (
        f"Prompt version: {prompt_version}\n"
        f"Scenario: {scenario_title}\n"
        f"Context: {context}\n"
        f"Learner role: {learner_role}\n"
        f"AI role: {ai_role}\n"
        f"AI character: {ai_character}\n"
        f"Level: {level}\n"
        f"Goal: {goal_text}\n\n"
        f"You are playing the role of {ai_role} in a roleplay conversation.\n"
        f"Your character name is {ai_character}.\n"
        f"LANGUAGE LEVEL: {level} — {level_instruction}\n\n"
        f"IMPLICIT ERROR CORRECTION:\n"
        f"{implicit_correction_instruction}\n\n"
        f"{implicit_correction_examples}\n\n"
        f"CONVERSATION RULES:\n"
        f"1. Stay in character as {ai_role} at all times.\n"
        f"2. Keep responses SHORT and NATURAL (match the level above).\n"
        f"3. Always move the conversation forward — ask a question or prompt the next action.\n"
        f"4. Do NOT correct grammar during conversation. Evaluation happens after.\n"
        f"5. If the learner goes off-topic, gently redirect: \"That's interesting! But let's get back to {scenario_title}...\"\n"
        f"6. If the learner uses inappropriate language: \"Let's keep it professional. Now, {goal_text}...\"\n"
        f"7. If the learner writes in Vietnamese, respond: \"Please try in English! I'll help you. [simple English prompt]\"\n"
        f"8. NEVER say you are an AI unless directly asked."
    )


def build_xml_prompt(
    instruction: str,
    examples: list[dict],
    output_format: str,
) -> str:
    """Build a structured prompt with XML tags.
    
    Args:
        instruction: Main instruction text (can include context)
        examples: List of dicts with 'input' and 'output' keys
        output_format: Expected output format description
        
    Returns:
        Formatted prompt with XML tags
    """
    prompt = f"<instruction>\n{instruction}\n</instruction>\n\n"
    
    if examples:
        prompt += "<examples>\n"
        for i, example in enumerate(examples, 1):
            prompt += f"<example {i}>\n"
            if "input" in example:
                prompt += f"Input: {example['input']}\n"
            if "output" in example:
                prompt += f"Output:\n{example['output']}\n"
            prompt += f"</example {i}>\n\n"
        prompt += "</examples>\n\n"
    
    prompt += f"<output_format>\n{output_format}\n</output_format>"
    
    return prompt


def escape_json_string(text: str) -> str:
    """Escape special characters for JSON string values.
    
    Converts newlines to \\n, quotes to \", etc.
    """
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
