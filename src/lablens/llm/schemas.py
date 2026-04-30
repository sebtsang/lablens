"""Pydantic schemas for validating Anthropic JSON output (CLAUDE.md §8)."""

from __future__ import annotations

from pydantic import BaseModel


class MechanismEntry(BaseModel):
    medication: str
    summary: str


class LlmInteractionResponse(BaseModel):
    mechanisms: list[MechanismEntry]
    cumulative_risk_note: str
