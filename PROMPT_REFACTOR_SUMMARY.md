# Prompt Refactor Summary - AWS Best Practices

## 🎯 Objective
Refactor prompt engineering for `structured_hint_generator.py` and `conversation_analyzer.py` to follow AWS Nova best practices and fix output format issues.

## 📚 Research Findings (AWS Docs)

### 1. Structured Output Best Practices
- **Tool Use + Constrained Decoding**: Automatically enforces JSON schema validity
- **Temperature = 0**: Use greedy decoding for structured output (not 0.3)
- **Reference**: https://docs.aws.amazon.com/nova/latest/userguide/concept-chapter-servicename.html

### 2. Few-Shot Prompting
- **Diverse Examples**: Cover common cases + edge cases
- **Match Complexity**: Examples should align with target task complexity
- **Ensure Relevance**: Examples directly relevant to problem
- **Reference**: https://docs.aws.amazon.com/nova/latest/userguide/prompting-examples.html

### 3. Prompt Structure (System + User Roles)
- **System Role**: Establishes behavioral parameters (optional but recommended)
- **User Role**: Conveys context, tasks, instructions, and examples
- **Reference**: https://docs.aws.amazon.com/nova/latest/userguide/prompting-text-understanding.html

### 4. Output Format
- **Prefilling**: Guide model response by prefilling assistant content
- **Explicit Schema**: Provide clear output format instructions
- **Avoid Escaped Unicode**: Can cause repetitive loops
- **Reference**: https://docs.aws.amazon.com/nova/latest/userguide/prompting-structured-output.html

## 🔧 Changes Made

### File 1: `src/domain/services/prompt_builder.py` (NEW)
**Purpose**: Reusable helper functions for structured prompts

```python
def build_xml_prompt(instruction, examples, output_format) -> str
def escape_json_string(text) -> str
```

### File 2: `src/domain/services/structured_hint_generator.py`

#### Changes:
1. **Split prompt into system + user roles**
   - `_build_system_prompt()`: Behavioral parameters (NEW)
   - `_build_user_prompt()`: Context + task + few-shot examples (REFACTORED)

2. **Few-shot examples** (2 diverse examples)
   - Example 1: Basic A1 level (morning routine)
   - Example 2: Intermediate B1 level (past weekend)

3. **Temperature = 0** (was 0.3)
   - AWS best practice for structured output

4. **System role in converse_stream()**
   - Added `system=[{"text": system_prompt}]`

5. **Updated method signatures**
   - `_call_bedrock_with_retry(system_prompt, user_prompt)`
   - `_call_bedrock(system_prompt, user_prompt)`

### File 3: `src/domain/services/conversation_analyzer.py`

#### Changes:
1. **System prompt refactored** (English-first)
   - Behavioral parameters in English
   - Clear role definition

2. **User prompt with few-shot examples** (2 diverse examples)
   - Example 1: A1 level (past tense error)
   - Example 2: A2 level (gerund error)

3. **Temperature = 0** (was 0.3)
   - AWS best practice for structured output

4. **Removed verbose Vietnamese instructions**
   - Moved to system role
   - User role now focused on task + examples

## ✅ Key Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **Prompt Structure** | Single prompt string | System + User roles |
| **Examples** | 1 example (verbose) | 2 diverse examples (concise) |
| **Temperature** | 0.3 | 0 (greedy decoding) |
| **Output Format** | Prompt-based | Tool use + constrained decoding |
| **Language** | Mixed Vietnamese/English | English instruction + Vietnamese examples |
| **Few-shot** | Implicit | Explicit with diverse cases |

## 🎓 AWS Best Practices Applied

✅ **Structured Output**: Tool use + constrained decoding  
✅ **Few-Shot Prompting**: Diverse, relevant examples  
✅ **Prompt Structure**: Clear system + user role separation  
✅ **Temperature**: 0 for greedy decoding  
✅ **Instruction Clarity**: Explicit, unambiguous guidance  
✅ **Output Schema**: JSON schema in tool config  

## 📊 Expected Outcomes

1. **Consistent JSON Output**: Constrained decoding ensures valid JSON
2. **Better Accuracy**: Few-shot examples guide model behavior
3. **Reduced Hallucination**: Clear system role + explicit examples
4. **Faster Generation**: Temperature = 0 (greedy decoding)
5. **Bilingual Balance**: Vietnamese explanation + English examples (no translation)

## 🔗 References

- AWS Nova Prompting: https://docs.aws.amazon.com/nova/latest/userguide/prompting.html
- Structured Output: https://docs.aws.amazon.com/nova/latest/userguide/concept-chapter-servicename.html
- Few-Shot Prompting: https://docs.aws.amazon.com/nova/latest/userguide/prompting-examples.html
- Text Understanding: https://docs.aws.amazon.com/nova/latest/userguide/prompting-text-understanding.html
