"""Pydantic models shared across the four MCP tools.

These mirror the contracts in CLAUDE.md §6.1-§6.4. Keep field names and shapes
stable — tools call each other through these models, and the Prompt Opinion
agent depends on the JSON shape.
"""

from typing import Literal

from pydantic import BaseModel, Field

from lablens.clinical.lab_loinc_codes import LabType

Urgency = Literal["URGENT", "SOON", "ROUTINE", "INSUFFICIENT_DATA"]
Trend = Literal["RISING", "FALLING", "STABLE", "INSUFFICIENT_DATA"]
InteractionDirection = Literal["INCREASES", "DECREASES", "VARIABLE"]
EvidenceStrength = Literal["WELL_ESTABLISHED", "MODERATE", "LIMITED"]


class Demographics(BaseModel):
    age: int
    sex: str


class ConditionRef(BaseModel):
    code: str
    display: str
    onset_date: str | None = None


class MedicationRef(BaseModel):
    code: str
    display: str
    dose: str | None = None
    frequency: str | None = None
    drug_class: str | None = None


class AllergyRef(BaseModel):
    substance: str
    reaction: str | None = None
    severity: str | None = None


class EncounterRef(BaseModel):
    date: str
    type: str
    reason: str | None = None


class PatientContext(BaseModel):
    """Output of get_patient_context (§6.1)."""

    patient_id: str
    demographics: Demographics
    active_conditions: list[ConditionRef] = Field(default_factory=list)
    active_medications: list[MedicationRef] = Field(default_factory=list)
    allergies: list[AllergyRef] = Field(default_factory=list)
    recent_encounters: list[EncounterRef] = Field(default_factory=list)


class LabValuePoint(BaseModel):
    value: float
    effective_date: str
    reference_low: float | None = None
    reference_high: float | None = None


class LabTrendResult(BaseModel):
    """Output of get_lab_trend (§6.2)."""

    lab_code: str
    lab_display: str
    unit: str
    values: list[LabValuePoint] = Field(default_factory=list)
    trend: Trend
    delta_from_baseline: float | None = None


class MedicationInteraction(BaseModel):
    medication_display: str
    drug_class: str
    direction: InteractionDirection
    mechanism_summary: str
    evidence_strength: EvidenceStrength


class MedicationInteractions(BaseModel):
    """Output of analyze_medication_lab_interactions (§6.3)."""

    interactions_found: list[MedicationInteraction] = Field(default_factory=list)
    cumulative_risk_note: str
    has_significant_interactions: bool


class ClassifierOutput(BaseModel):
    """Output of classify_lab_followup_urgency (§6.4)."""

    urgency: Urgency
    rule_trace: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    recommended_review_path: str
    safety_label: str


__all__ = [
    "AllergyRef",
    "ClassifierOutput",
    "ConditionRef",
    "Demographics",
    "EncounterRef",
    "EvidenceStrength",
    "InteractionDirection",
    "LabTrendResult",
    "LabType",
    "LabValuePoint",
    "MedicationInteraction",
    "MedicationInteractions",
    "MedicationRef",
    "PatientContext",
    "Trend",
    "Urgency",
]
