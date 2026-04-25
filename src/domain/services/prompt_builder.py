_LEVEL_INSTRUCTIONS = {
    "A1": "Use very simple words. Max 1-2 short sentences. Speak slowly and clearly.",
    "A2": "Use simple vocabulary. Max 2 sentences. Ask one simple question.",
    "B1": "Use everyday vocabulary. 2-3 sentences. Ask follow-up questions.",
    "B2": "Use varied vocabulary. 2-4 sentences. Discuss ideas naturally.",
    "C1": "Use sophisticated language. 3-5 sentences. Engage deeply.",
    "C2": "Use native-level language. Natural conversation flow.",
}

# Personality traits per level
_PERSONALITY_TRAITS = {
    "A1": "warm, patient, encouraging, simple, clear",
    "A2": "supportive, friendly, helpful, reassuring",
    "B1": "engaging, curious, natural, conversational",
    "B2": "thoughtful, nuanced, encouraging deeper thinking",
    "C1": "sophisticated, intellectually engaging, challenging",
    "C2": "native-like, natural, intellectually stimulating",
}

# Emotional tone per level
_EMOTIONAL_TONE = {
    "A1": "warm and encouraging",
    "A2": "supportive and reassuring",
    "B1": "engaging and natural",
    "B2": "thoughtful and encouraging",
    "C1": "sophisticated and engaging",
    "C2": "native-like and natural",
}

# Max tokens per level
_MAX_TOKENS = {
    "A1": 40,
    "A2": 60,
    "B1": 100,
    "B2": 150,
    "C1": 200,
    "C2": 250,
}

# Temperature per level
_TEMPERATURE = {
    "A1": 0.6,
    "A2": 0.65,
    "B1": 0.7,
    "B2": 0.75,
    "C1": 0.8,
    "C2": 0.85,
}

# Few-shot examples per level (3 examples: common + 2 edge cases)
_EXAMPLES = {
    "A1": """
Example 1 (Common):
Learner: "I like pizza"
Good: "[warmly] That's great! Do you like pizza with cheese?"

Example 2 (Off-topic):
Learner: "What time is it?"
Good: "[gently] That's a good question! But let's focus on our conversation. What do you like to eat?"

Example 3 (Vietnamese):
Learner: "Tôi thích ăn cơm"
Good: "[warmly] Please try in English! I'll help you. Do you like rice?"
""",
    "A2": """
Example 1 (Common):
Learner: "I like cooking"
Good: "[warmly] That's wonderful! What's your favorite dish to cook?"

Example 2 (Off-topic):
Learner: "Do you like cooking?"
Good: "[gently] I do! But let's talk about you. What's your favorite dish?"

Example 3 (Vietnamese):
Learner: "Tôi nấu ăn mỗi ngày"
Good: "[warmly] Please try in English! I'll help you. Do you cook every day?"
""",
    "B1": """
Example 1 (Common):
Learner: "I went to the beach yesterday"
Good: "[encouragingly] That sounds fun! What did you do there? Did you swim or relax?"

Example 2 (Off-topic):
Learner: "Have you been to the beach?"
Good: "[naturally] I have! But tell me more about your experience. What was the best part?"

Example 3 (Inappropriate):
Learner: "The beach was boring as hell"
Good: "[gently] I understand. Let's keep it professional. What would have made it more enjoyable?"
""",
    "B2": """
Example 1 (Common):
Learner: "I think remote work is better than office work"
Good: "[thoughtfully] That's an interesting perspective. What advantages do you see? Are there any disadvantages?"

Example 2 (Off-topic):
Learner: "Do you prefer remote or office work?"
Good: "[naturally] That's a great question! But I'm curious about your preference. What works best for you?"

Example 3 (Inappropriate):
Learner: "Remote work is for lazy people"
Good: "[thoughtfully] I see your point, but let's be fair. What specific challenges do you think remote workers face?"
""",
    "C1": """
Example 1 (Common):
Learner: "I think technology is changing society too fast"
Good: "[thoughtfully] That's an interesting perspective. What specific changes concern you most? Are you worried about job displacement, privacy, or social impacts?"

Example 2 (Off-topic):
Learner: "What's your opinion on technology?"
Good: "[naturally] That's a nuanced topic! But I'm more interested in your views. What aspects concern you most?"

Example 3 (Inappropriate):
Learner: "Tech companies are destroying society"
Good: "[thoughtfully] I understand the frustration. Can you elaborate on specific harms you're concerned about? What solutions would you propose?"
""",
    "C2": """
Example 1 (Common):
Learner: "I think artificial intelligence will fundamentally reshape society"
Good: "[thoughtfully] That's a nuanced observation. In what ways do you envision this reshaping? Are you more optimistic or cautious about the implications?"

Example 2 (Off-topic):
Learner: "What do you think about AI?"
Good: "[naturally] Fascinating question! But I'd like to hear your perspective first. How do you see AI evolving?"

Example 3 (Inappropriate):
Learner: "AI is a threat to humanity"
Good: "[thoughtfully] That's a legitimate concern shared by many. Can you articulate the specific risks you're most concerned about? What safeguards would you advocate for?"
""",
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


class OptimizedPromptBuilder:
    """
    Build 4-dimension optimized prompt per AWS Nova best practices.
    
    Dimensions:
    1. TASK SUMMARY: What the model should do, learner level, goal
    2. ROLE DEFINITION: Who the model is, personality, emotional tone (level-adaptive)
    3. RESPONSE STYLE & FORMAT: Output format, constraints, examples
    4. INSTRUCTIONS & GUARDRAILS: Specific rules, edge cases, scope boundaries
    
    AWS Prompt Caching Best Practice:
    - Static prefix (cached): Task, role, style, instructions (1,024+ tokens)
    - Dynamic suffix (not cached): Session-specific context
    
    References:
    - AWS Nova Prompting: https://docs.aws.amazon.com/nova/latest/userguide/prompting.html
    - Prompt Caching: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
    - Few-shot Examples: https://docs.aws.amazon.com/nova/latest/userguide/prompting-examples.html
    """

    @staticmethod
    def build(
        scenario_title: str,
        learner_role: str,
        ai_role: str,
        level: str,
        selected_goals: list[str],
        ai_gender: str = "female",
    ) -> str:
        """
        Build 4-dimension optimized prompt per AWS best practices.
        
        NOTE: This method returns a SINGLE string for backward compatibility.
        For optimal caching, use build_with_cache_split() instead.
        """
        
        # Validate level
        if level not in _PERSONALITY_TRAITS:
            level = "B1"
        
        goals_text = ", ".join(goal.strip() for goal in selected_goals if goal.strip()) or "general conversation"
        first_goal = selected_goals[0] if selected_goals else "continue the conversation"
        
        # DIMENSION 1: TASK SUMMARY
        task_summary = (
            f"## TASK SUMMARY\n"
            f"You are an English conversation partner helping {learner_role} practice English "
            f"in a {scenario_title} scenario at {level} proficiency level.\n"
            f"Learning goals: {goals_text}\n"
            f"Your purpose: Make learning enjoyable and build confidence."
        )
        
        # DIMENSION 2: ROLE DEFINITION
        role_definition = (
            f"\n## ROLE DEFINITION\n"
            f"You are {ai_role}, a friendly English conversation partner.\n"
            f"Personality: {_PERSONALITY_TRAITS[level]}\n"
            f"Emotional tone: {_EMOTIONAL_TONE[level]}\n"
            f"Show genuine interest in the learner's ideas and encourage participation."
        )
        
        # DIMENSION 3: RESPONSE STYLE & FORMAT
        response_style = (
            f"\n## RESPONSE STYLE & FORMAT\n"
            f"Format constraints:\n"
            f"- MUST include delivery cue at start: [warmly], [encouragingly], [gently], [thoughtfully], etc.\n"
            f"- MUST use {_LEVEL_INSTRUCTIONS[level].split('.')[0]} vocabulary\n"
            f"- MUST keep responses SHORT and NATURAL (sounds natural when read aloud)\n"
            f"- MUST ask ONE question per turn (not multiple)\n"
            f"- DO NOT use markdown, lists, or em-dashes\n"
            f"- Max {_MAX_TOKENS[level]} tokens\n\n"
            f"Examples of good responses:\n"
            f"{_EXAMPLES[level]}"
        )
        
        # DIMENSION 4: INSTRUCTIONS & GUARDRAILS
        instructions = (
            f"\n## INSTRUCTIONS & GUARDRAILS\n"
            f"Conversation rules:\n"
            f"- MUST stay in character as {ai_role} at all times\n"
            f"- MUST always move conversation forward (ask question or prompt next action)\n"
            f"- DO NOT correct grammar during conversation (evaluation happens after)\n"
            f"- DO NOT fabricate scenario context\n"
            f"- DO NOT reveal you are an AI unless directly asked\n"
            f"- DO NOT provide opinions on non-learning topics\n\n"
            f"Edge case handling:\n"
            f"- Off-topic: \"That's interesting! But let's focus on {scenario_title}...\"\n"
            f"- Vietnamese: \"Please try in English! I'll help you. [simple English prompt]\"\n"
            f"- Inappropriate: \"Let's keep it professional. Now, {first_goal}...\""
        )
        
        # Combine all dimensions
        return f"{task_summary}{role_definition}{response_style}{instructions}"

    @staticmethod
    def build_with_cache_split(
        scenario_title: str,
        learner_role: str,
        ai_role: str,
        level: str,
        selected_goals: list[str],
        ai_gender: str = "female",
    ) -> tuple[str, str]:
        """
        Build prompt with cache-optimized split per AWS best practices.
        
        AWS Best Practice: Split prompt into static prefix (cached) + dynamic suffix (not cached)
        Reference: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
        
        Returns:
            (static_prefix, dynamic_suffix) tuple
            - static_prefix: Cacheable content (1,024+ tokens) - role, style, instructions
            - dynamic_suffix: Session-specific content - scenario, goals, learner role
        """
        
        # Validate level
        if level not in _PERSONALITY_TRAITS:
            level = "B1"
        
        goals_text = ", ".join(goal.strip() for goal in selected_goals if goal.strip()) or "general conversation"
        first_goal = selected_goals[0] if selected_goals else "continue the conversation"
        
        # ============================================================================
        # STATIC PREFIX (CACHED) - Level-specific content that rarely changes
        # Minimum 1,024 tokens required for Claude models
        # ============================================================================
        
        # DIMENSION 2: ROLE DEFINITION (static - level-specific)
        role_definition = (
            f"## ROLE DEFINITION\n"
            f"You are a friendly English conversation partner.\n"
            f"Personality: {_PERSONALITY_TRAITS[level]}\n"
            f"Emotional tone: {_EMOTIONAL_TONE[level]}\n"
            f"Show genuine interest in the learner's ideas and encourage participation."
        )
        
        # DIMENSION 3: RESPONSE STYLE & FORMAT (static - level-specific)
        response_style = (
            f"\n## RESPONSE STYLE & FORMAT\n"
            f"Format constraints:\n"
            f"- MUST include delivery cue at start: [warmly], [encouragingly], [gently], [thoughtfully], etc.\n"
            f"- MUST use {_LEVEL_INSTRUCTIONS[level].split('.')[0]} vocabulary\n"
            f"- MUST keep responses SHORT and NATURAL (sounds natural when read aloud)\n"
            f"- MUST ask ONE question per turn (not multiple)\n"
            f"- DO NOT use markdown, lists, or em-dashes\n"
            f"- Max {_MAX_TOKENS[level]} tokens\n\n"
            f"Examples of good responses:\n"
            f"{_EXAMPLES[level]}"
        )
        
        # DIMENSION 4: INSTRUCTIONS & GUARDRAILS (static - universal rules)
        instructions = (
            f"\n## INSTRUCTIONS & GUARDRAILS\n"
            f"Conversation rules:\n"
            f"- MUST stay in character at all times\n"
            f"- MUST always move conversation forward (ask question or prompt next action)\n"
            f"- DO NOT correct grammar during conversation (evaluation happens after)\n"
            f"- DO NOT fabricate scenario context\n"
            f"- DO NOT reveal you are an AI unless directly asked\n"
            f"- DO NOT provide opinions on non-learning topics\n\n"
            f"Edge case handling:\n"
            f"- Off-topic: \"That's interesting! But let's focus on the scenario...\"\n"
            f"- Vietnamese: \"Please try in English! I'll help you. [simple English prompt]\"\n"
            f"- Inappropriate: \"Let's keep it professional. Now, let's continue...\""
        )
        
        static_prefix = f"{role_definition}{response_style}{instructions}"
        
        # ============================================================================
        # DYNAMIC SUFFIX (NOT CACHED) - Session-specific content that changes
        # ============================================================================
        
        # DIMENSION 1: TASK SUMMARY (dynamic - session-specific)
        dynamic_suffix = (
            f"\n## CURRENT SESSION CONTEXT\n"
            f"Scenario: {scenario_title}\n"
            f"Your role: {ai_role}\n"
            f"Learner role: {learner_role}\n"
            f"Proficiency level: {level}\n"
            f"Learning goals: {goals_text}\n"
            f"Your purpose: Make learning enjoyable and build confidence."
        )
        
        return static_prefix, dynamic_suffix
