"""Anthropic client wrapper for the single LLM call site.

Per CLAUDE.md §8: model claude-opus-4-7, temperature 0.2, max 800 tokens. Validates
the JSON output against `LlmInteractionResponse`. Retries up to twice on validation
failure (per §8); after that, returns a fallback response with a warning logged.

Per CLAUDE.md §17, this is the ONLY LLM call in the system. Do not call from
other tools.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Protocol

from anthropic import Anthropic
from pydantic import ValidationError

from lablens.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from lablens.llm.schemas import LlmInteractionResponse, MechanismEntry

_log = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 800
MAX_RETRIES = 2


class _AnthropicLike(Protocol):
    """Subset of the Anthropic client we depend on (for testability)."""

    @property
    def messages(self) -> object: ...


def _extract_json_text(message_content: list[object]) -> str:
    """Pull the first text block out of an Anthropic Messages response."""
    for block in message_content:
        if hasattr(block, "type") and getattr(block, "type", None) == "text":
            text = getattr(block, "text", "")
            if isinstance(text, str):
                return text
    return ""


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        # Strip leading ```json or ``` and trailing ```
        first_newline = stripped.find("\n")
        if first_newline != -1:
            stripped = stripped[first_newline + 1 :]
        if stripped.endswith("```"):
            stripped = stripped[:-3]
    return stripped.strip()


def _fallback_response(identified: list[tuple[str, str, str]]) -> LlmInteractionResponse:
    return LlmInteractionResponse(
        mechanisms=[
            MechanismEntry(
                medication=name,
                summary=(
                    f"Mechanism not well established in this output (LLM validation fallback). "
                    f"{name} is classified as {drug_class}, direction {direction}."
                ),
            )
            for name, drug_class, direction in identified
        ],
        cumulative_risk_note=(
            "Cumulative risk narration unavailable; the deterministic drug-class detection "
            "still flagged the interactions above."
        ),
    )


def call_interaction_llm(
    *,
    lab_type: str,
    identified_interactions: list[tuple[str, str, str]],
    client: Anthropic | None = None,
) -> LlmInteractionResponse:
    """Single LLM call site. Returns validated `LlmInteractionResponse` or fallback."""
    if not identified_interactions:
        return LlmInteractionResponse(
            mechanisms=[],
            cumulative_risk_note="No identified medication interactions for this lab type.",
        )

    api_client = client or Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    user_prompt = build_user_prompt(lab_type, identified_interactions)

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            message = api_client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw_text = _extract_json_text(list(message.content))
            payload = _strip_code_fences(raw_text)
            data = json.loads(payload)
            return LlmInteractionResponse.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            _log.warning(
                "interaction_llm_validation_failed",
                extra={"attempt": attempt + 1, "lab_type": lab_type},
            )
            continue

    _log.warning(
        "interaction_llm_all_retries_failed",
        extra={"lab_type": lab_type, "error": str(last_error) if last_error else "unknown"},
    )
    return _fallback_response(identified_interactions)
