"""Knowledge extractor using LLMs via LiteLLM.

Extracts facts, decisions, and learnings from conversations using
multiple LLM providers with fallback support.
"""

import json
import logging
import os
from dataclasses import dataclass

from oxmemory.core.models import Memory, MemoryType
from oxmemory.extraction.prompts import EXTRACTION_PROMPTS

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of knowledge extraction."""

    facts: list[dict]
    decisions: list[dict]
    learnings: list[dict]
    raw_response: str | None = None
    error: str | None = None


@dataclass
class LLMProvider:
    """LLM provider configuration."""

    name: str
    model: str
    api_key_env: str | None = None
    host_env: str | None = None  # Environment variable for host
    default_host: str | None = None

    def get_model_string(self) -> str:
        """Get the LiteLLM model string."""
        if self.name == "ollama":
            return f"ollama/{self.model}"
        elif self.name == "groq":
            return f"groq/{self.model}"
        elif self.name == "gemini":
            return f"gemini/{self.model}"
        elif self.name == "openrouter":
            return f"openrouter/{self.model}"
        elif self.name == "openai":
            return self.model
        else:
            return f"{self.name}/{self.model}"

    def get_host(self) -> str | None:
        """Get the host URL from env or default."""
        if self.host_env:
            return os.environ.get(self.host_env, self.default_host)
        return self.default_host

    def is_available(self) -> bool:
        """Check if this provider is configured."""
        if self.name == "ollama":
            # Ollama available if host is set via env or default exists
            host = self.get_host()
            return host is not None

        if self.api_key_env:
            return bool(os.environ.get(self.api_key_env))

        return False


# Default providers in priority order
DEFAULT_PROVIDERS = [
    LLMProvider(
        name="ollama",
        model="llama3.2:3b",
        host_env="OLLAMA_API_BASE",
        default_host="http://localhost:11434",
    ),
    LLMProvider(
        name="groq",
        model="llama-3.3-70b-versatile",
        api_key_env="GROQ_API_KEY",
    ),
    LLMProvider(
        name="openrouter",
        model="meta-llama/llama-3.3-70b-instruct",
        api_key_env="OPENROUTER_API_KEY",
    ),
    LLMProvider(
        name="gemini",
        model="gemini-2.0-flash",
        api_key_env="GEMINI_API_KEY",
    ),
]


class KnowledgeExtractor:
    """Extracts knowledge from conversations using LLMs.

    Supports multiple providers with automatic fallback:
    1. Ollama (local, unlimited)
    2. Groq (fast, free tier)
    3. Gemini (Google, free tier)
    4. OpenAI (if configured)
    """

    def __init__(
        self,
        providers: list[LLMProvider] | None = None,
        max_extractions_per_call: int = 5,
        confidence_threshold: float = 0.7,
    ):
        """Initialize the extractor.

        Args:
            providers: List of LLM providers in priority order.
            max_extractions_per_call: Maximum number of facts/decisions to extract per call.
            confidence_threshold: Minimum confidence to accept an extraction.
        """
        self.providers = providers or DEFAULT_PROVIDERS
        self.max_extractions = max_extractions_per_call
        self.confidence_threshold = confidence_threshold
        self._litellm = None

    @property
    def litellm(self):
        """Lazy-load litellm."""
        if self._litellm is None:
            import litellm

            litellm.set_verbose = False
            self._litellm = litellm
        return self._litellm

    def _get_available_provider(self) -> LLMProvider | None:
        """Get the first available provider."""
        for provider in self.providers:
            if provider.is_available():
                return provider
        return None

    async def _call_llm(
        self,
        prompt: str,
        system_prompt: str | None = None,
        provider: LLMProvider | None = None,
    ) -> str | None:
        """Call LLM with the given prompt.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.
            provider: Specific provider to use.

        Returns:
            LLM response text, or None on failure.
        """
        if provider is None:
            provider = self._get_available_provider()

        if provider is None:
            logger.warning("No LLM provider available")
            return None

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            # Set environment for Ollama if needed
            if provider.name == "ollama":
                host = provider.get_host()
                if host:
                    os.environ["OLLAMA_API_BASE"] = host

            response = await self.litellm.acompletion(
                model=provider.get_model_string(),
                messages=messages,
                temperature=0.3,  # Lower for more consistent extraction
                max_tokens=2000,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.warning(f"LLM call failed with {provider.name}: {e}")

            # Try next provider
            current_idx = self.providers.index(provider) if provider in self.providers else -1
            for next_provider in self.providers[current_idx + 1 :]:
                if next_provider.is_available():
                    logger.info(f"Falling back to {next_provider.name}")
                    return await self._call_llm(prompt, system_prompt, next_provider)

            return None

    def _parse_extraction_response(self, response: str) -> ExtractionResult:
        """Parse LLM response into structured extraction result.

        Args:
            response: Raw LLM response.

        Returns:
            ExtractionResult with parsed facts, decisions, learnings.
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            # Filter by confidence threshold
            facts = [
                f
                for f in data.get("facts", [])
                if f.get("confidence", 0) >= self.confidence_threshold
            ][: self.max_extractions]

            decisions = [
                d
                for d in data.get("decisions", [])
                if d.get("confidence", 0) >= self.confidence_threshold
            ][: self.max_extractions]

            learnings = [
                learning
                for learning in data.get("learnings", [])
                if learning.get("confidence", 0) >= self.confidence_threshold
            ][: self.max_extractions]

            return ExtractionResult(
                facts=facts,
                decisions=decisions,
                learnings=learnings,
                raw_response=response,
            )

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"Failed to parse extraction response: {e}")
            return ExtractionResult(
                facts=[],
                decisions=[],
                learnings=[],
                raw_response=response,
                error=str(e),
            )

    async def extract(self, conversation: str) -> ExtractionResult:
        """Extract knowledge from a conversation.

        Args:
            conversation: The conversation text to analyze.

        Returns:
            ExtractionResult with extracted facts, decisions, learnings.
        """
        prompt = EXTRACTION_PROMPTS["extract"].format(conversation=conversation)
        system_prompt = EXTRACTION_PROMPTS["system"]

        response = await self._call_llm(prompt, system_prompt)

        if response is None:
            return ExtractionResult(
                facts=[],
                decisions=[],
                learnings=[],
                error="No LLM response",
            )

        return self._parse_extraction_response(response)

    async def summarize_session(self, conversation: str) -> str | None:
        """Summarize a conversation session.

        Args:
            conversation: The conversation to summarize.

        Returns:
            Summary string, or None on failure.
        """
        prompt = EXTRACTION_PROMPTS["summarize"].format(conversation=conversation)
        return await self._call_llm(prompt)

    def extraction_to_memories(self, result: ExtractionResult) -> list[Memory]:
        """Convert extraction result to Memory objects.

        Args:
            result: Extraction result to convert.

        Returns:
            List of Memory objects.
        """
        memories = []

        for fact in result.facts:
            memories.append(
                Memory(
                    content=fact.get("content", ""),
                    type=MemoryType.FACT,
                    tags=fact.get("tags", []),
                    source="extraction",
                    salience=fact.get("confidence", 0.5),
                )
            )

        for decision in result.decisions:
            memories.append(
                Memory(
                    content=decision.get("content", ""),
                    type=MemoryType.DECISION,
                    tags=decision.get("tags", []),
                    source="extraction",
                    salience=decision.get("confidence", 0.5),
                )
            )

        for learning in result.learnings:
            memories.append(
                Memory(
                    content=learning.get("content", ""),
                    type=MemoryType.LEARNING,
                    tags=learning.get("tags", []),
                    source="extraction",
                    salience=learning.get("confidence", 0.5),
                )
            )

        return memories

    def is_available(self) -> bool:
        """Check if any LLM provider is available.

        Returns:
            True if at least one provider is configured.
        """
        return self._get_available_provider() is not None
