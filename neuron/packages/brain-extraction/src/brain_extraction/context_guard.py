from __future__ import annotations


class ContextLimitExceeded(Exception):
    """Raised before an LLM call whose prompt would exceed the configured context
    limit. No truncated output is ever accepted as a result (F0001-S0003
    acceptance criterion 4)."""

    code = "context_limit_exceeded"

    def __init__(self, prompt_tokens: int, limit: int, reserve_for_output: int) -> None:
        self.prompt_tokens = prompt_tokens
        self.limit = limit
        self.reserve_for_output = reserve_for_output
        super().__init__(
            f"prompt_tokens={prompt_tokens} exceeds budget "
            f"{limit - reserve_for_output} (limit={limit}, reserve_for_output={reserve_for_output})"
        )


class ContextGuard:
    """Client-side context-length check for the OpenAI-compatible backend
    (`microsoft/Phi-4-mini-instruct`, 4,096-token context, ADR-0055)."""

    def __init__(self, limit: int, reserve_for_output: int = 512) -> None:
        self.limit = limit
        self.reserve_for_output = reserve_for_output

    def check(self, prompt_tokens: int) -> None:
        if prompt_tokens > self.limit - self.reserve_for_output:
            raise ContextLimitExceeded(prompt_tokens, self.limit, self.reserve_for_output)
