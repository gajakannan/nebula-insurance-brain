"""Compatibility import for the F0001 adapter's historical name.

This is the direct OpenAI-compatible baseline, not the upstream Docling-Graph
pipeline. New callers should import OpenAICompatibleExtractionAdapter.
"""

from brain_extraction.openai_compatible_adapter import (
    OpenAICompatibleExtractionAdapter as DoclingGraphAdapter,
)

__all__ = ["DoclingGraphAdapter"]
