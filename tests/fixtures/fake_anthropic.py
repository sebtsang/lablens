"""Fake Anthropic client for tests of the medication-interaction LLM call."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class _TextBlock:
    text: str
    type: str = "text"


@dataclass
class _Message:
    content: list[_TextBlock]


class _MessagesEndpoint:
    def __init__(self, response_text: str | list[str]) -> None:
        # Support a sequence of responses for retry tests
        self._responses = [response_text] if isinstance(response_text, str) else list(response_text)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _Message:
        self.calls.append(kwargs)
        idx = min(len(self.calls) - 1, len(self._responses) - 1)
        return _Message(content=[_TextBlock(text=self._responses[idx])])


class FakeAnthropic:
    def __init__(self, response_text: str | list[str]) -> None:
        self.messages = _MessagesEndpoint(response_text)
