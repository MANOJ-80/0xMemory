"""Extraction module - LLM-based knowledge extraction."""

from oxmemory.extraction.extractor import KnowledgeExtractor
from oxmemory.extraction.prompts import EXTRACTION_PROMPTS

__all__ = [
    "KnowledgeExtractor",
    "EXTRACTION_PROMPTS",
]
