"""LLM call site for analyze_medication_lab_interactions (CLAUDE.md §8).

The single LLM call point in the system. Three backends are supported:

- **Gemini** (default) — uses GEMINI_API_KEY (or GOOGLE_API_KEY). Free via Prompt Opinion.
- **Anthropic** — uses ANTHROPIC_API_KEY. claude-opus-4-7.
- **Ollama** — uses OLLAMA_BASE_URL (default http://localhost:11434) and OLLAMA_MODEL
  (default llama3.2). For local development.

Provider is selected by `LABLENS_LLM_PROVIDER` env var. If unset, defaults to "gemini".
The provider dispatch is bypassed when an `anthropic_client` is passed explicitly
(test path) — that keeps the existing test fixtures working without churn.
"""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING

import httpx
from anthropic import Anthropic
from pydantic import ValidationError

from lablens.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from lablens.llm.schemas import LlmInteractionResponse, MechanismEntry

if TYPE_CHECKING:
    from collections.abc import Callable

_log = logging.getLogger(__name__)

# Anthropic config
ANTHROPIC_MODEL = "claude-opus-4-7"
# Gemini config. gemini-2.5-flash is the default; can override with GEMINI_MODEL env.
# (gemini-2.0-flash is intentionally NOT the default — its free tier is limit:0
# on freshly-created Google AI Studio projects as of April 2026.)
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash"
# Ollama config
OLLAMA_DEFAULT_MODEL = "llama3.2"
OLLAMA_DEFAULT_URL = "http://localhost:11434"

DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS = 800
MAX_RETRIES = 2


# ---------------------------------------------------------------------------
# Per-provider completers — each takes (system, user) and returns raw text
# ---------------------------------------------------------------------------


def _gemini_complete(system: str, user: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) must be set for Gemini provider")
    model_name = os.environ.get("GEMINI_MODEL", GEMINI_DEFAULT_MODEL)
    # Lazy import so this module can load even if google-genai isn't installed
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    config_kwargs: dict[str, object] = {
        "system_instruction": system,
        "temperature": DEFAULT_TEMPERATURE,
        "max_output_tokens": DEFAULT_MAX_TOKENS,
        "response_mime_type": "application/json",
    }
    # 2.5-series Gemini models use "thinking tokens" by default and can spend
    # the entire output budget on reasoning before producing JSON. Disable it
    # for our use case — we want fast, predictable JSON-out.
    if "2.5" in model_name or "3" in model_name:
        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    response = client.models.generate_content(
        model=model_name,
        contents=user,
        config=types.GenerateContentConfig(**config_kwargs),  # type: ignore[arg-type]
    )
    return response.text or ""


def _anthropic_complete(system: str, user: str, *, client: Anthropic | None = None) -> str:
    api_client = client or Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    message = api_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        temperature=DEFAULT_TEMPERATURE,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    for block in message.content:
        if hasattr(block, "type") and getattr(block, "type", None) == "text":
            text = getattr(block, "text", "")
            if isinstance(text, str):
                return text
    return ""


def _ollama_complete(system: str, user: str) -> str:
    base_url = os.environ.get("OLLAMA_BASE_URL", OLLAMA_DEFAULT_URL).rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL)
    response = httpx.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "options": {"temperature": DEFAULT_TEMPERATURE},
        },
        timeout=120.0,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "")


# ---------------------------------------------------------------------------
# Top-level call site
# ---------------------------------------------------------------------------


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
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


def _resolve_provider(anthropic_client: Anthropic | None) -> str:
    if anthropic_client is not None:
        return "anthropic"
    name = os.environ.get("LABLENS_LLM_PROVIDER", "gemini").strip().lower()
    if name not in {"gemini", "anthropic", "ollama"}:
        raise ValueError(
            f"Unknown LABLENS_LLM_PROVIDER: {name!r}. Expected one of: gemini, anthropic, ollama"
        )
    return name


def _completer_for(provider: str, anthropic_client: Anthropic | None) -> Callable[[str, str], str]:
    if provider == "gemini":
        return _gemini_complete
    if provider == "ollama":
        return _ollama_complete
    # provider == "anthropic"
    return lambda system, user: _anthropic_complete(system, user, client=anthropic_client)


def call_interaction_llm(
    *,
    lab_type: str,
    identified_interactions: list[tuple[str, str, str]],
    anthropic_client: Anthropic | None = None,
) -> LlmInteractionResponse:
    """Single LLM call site.

    Provider selection:
    - Pass `anthropic_client` explicitly (e.g. in tests) → uses Anthropic with that client
    - Otherwise read `LABLENS_LLM_PROVIDER` (gemini | anthropic | ollama; default gemini)

    Validates the JSON output with `LlmInteractionResponse`. Retries up to twice
    on validation failure (per CLAUDE.md §8); after that returns a fallback.
    """
    if not identified_interactions:
        return LlmInteractionResponse(
            mechanisms=[],
            cumulative_risk_note="No identified medication interactions for this lab type.",
        )

    provider = _resolve_provider(anthropic_client)
    completer = _completer_for(provider, anthropic_client)
    user_prompt = build_user_prompt(lab_type, identified_interactions)

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            raw_text = completer(SYSTEM_PROMPT, user_prompt)
            payload = _strip_code_fences(raw_text)
            data = json.loads(payload)
            return LlmInteractionResponse.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            _log.warning(
                "interaction_llm_validation_failed",
                extra={"attempt": attempt + 1, "lab_type": lab_type, "provider": provider},
            )
            continue

    _log.warning(
        "interaction_llm_all_retries_failed",
        extra={
            "lab_type": lab_type,
            "provider": provider,
            "error": str(last_error) if last_error else "unknown",
        },
    )
    return _fallback_response(identified_interactions)
