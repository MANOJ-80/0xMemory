"""Prompt templates for knowledge extraction."""

# System prompt for extraction
EXTRACTION_SYSTEM_PROMPT = """You are a knowledge extraction assistant. Your job is to analyze conversations and extract:

1. **Facts** - Concrete, verifiable information about the project (technical details, configurations, constraints)
2. **Decisions** - Choices made with their rationale (why something was chosen over alternatives)
3. **Learnings** - Lessons learned, gotchas, insights from experience

Rules:
- Extract ONLY information explicitly stated or clearly implied
- Do NOT make assumptions or add information not in the conversation
- Each extracted item should be self-contained and understandable without context
- Skip trivial or obvious information
- Focus on project-specific knowledge that would be valuable to remember"""

# Prompt for extracting facts and decisions
FACT_EXTRACTION_PROMPT = """Analyze this conversation and extract important facts and decisions.

Return your response as JSON with this structure:
```json
{{
  "facts": [
    {{
      "content": "The specific fact",
      "tags": ["tag1", "tag2"],
      "confidence": 0.9
    }}
  ],
  "decisions": [
    {{
      "content": "What was decided and why",
      "tags": ["tag1"],
      "confidence": 0.85
    }}
  ],
  "learnings": [
    {{
      "content": "Lesson learned or insight",
      "tags": ["tag1"],
      "confidence": 0.8
    }}
  ]
}}
```

Confidence should be 0.0-1.0 based on how clearly the information was stated.
Only include items with confidence >= 0.7.
Return empty arrays if nothing worth extracting.

CONVERSATION:
{conversation}"""

# Prompt for summarizing a session
SESSION_SUMMARY_PROMPT = """Summarize this conversation in 2-3 sentences, focusing on:
- What was discussed
- Key outcomes or decisions
- Any action items or next steps

Keep it concise and factual.

CONVERSATION:
{conversation}"""

# Prompt for checking if content is similar/duplicate
DEDUP_PROMPT = """Compare these two pieces of information and determine if they are semantically the same or very similar.

EXISTING: {existing}
NEW: {new}

Return JSON:
```json
{{
  "is_duplicate": true/false,
  "similarity": 0.0-1.0,
  "reason": "brief explanation"
}}
```"""

EXTRACTION_PROMPTS = {
    "system": EXTRACTION_SYSTEM_PROMPT,
    "extract": FACT_EXTRACTION_PROMPT,
    "summarize": SESSION_SUMMARY_PROMPT,
    "dedup": DEDUP_PROMPT,
}
