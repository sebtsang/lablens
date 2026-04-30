"""MCP tool: analyze_medication_lab_interactions (CLAUDE.md §6.3).

The differentiator. Two-step pipeline:

1. **Deterministic step (no LLM):** classify each active medication into a drug
   class via `DRUG_CLASS_LOOKUP`, identify which classes interact with the
   requested lab type, and assign the direction of effect.
2. **LLM step (single call site):** generate plain-language mechanism summaries
   and a cumulative risk note. The LLM is constrained to narration only — it
   cannot add medications or invent drug classes.

This is the ONLY LLM call site in the system per CLAUDE.md §17.
"""

from __future__ import annotations

from typing import TypedDict

from anthropic import Anthropic

from lablens.clinical.drug_classes import DRUG_CLASS_LOOKUP, lookup_drug_class
from lablens.clinical.lab_loinc_codes import LabType
from lablens.clinical.models import (
    EvidenceStrength,
    InteractionDirection,
    MedicationInteraction,
    MedicationInteractions,
    MedicationRef,
)
from lablens.llm.client import call_interaction_llm

# Direction of effect by drug class for each lab type. Lookup-only; the LLM
# does not get to invent these.
_DIRECTIONS: dict[LabType, dict[str, InteractionDirection]] = {
    "POTASSIUM": {
        "ACE_INHIBITOR": "INCREASES",
        "ARB": "INCREASES",
        "POTASSIUM_SPARING_DIURETIC": "INCREASES",
        "NSAID": "INCREASES",
    },
    "CREATININE": {
        "ACE_INHIBITOR": "INCREASES",
        "ARB": "INCREASES",
        "NSAID": "INCREASES",
        "NEPHROTOXIC_ANTIBIOTIC": "INCREASES",
        "AMINOGLYCOSIDE": "INCREASES",
        "CALCINEURIN_INHIBITOR": "INCREASES",
    },
    "HBA1C": {
        "CORTICOSTEROID": "INCREASES",
        "ATYPICAL_ANTIPSYCHOTIC": "INCREASES",
        "BIGUANIDE": "DECREASES",
        "INSULIN": "DECREASES",
    },
}

# Evidence strength is a fixed lookup; "WELL_ESTABLISHED" is the default for
# the table entries since they're standard pharmacology textbook material.
_EVIDENCE_BY_CLASS: dict[str, EvidenceStrength] = {
    "ACE_INHIBITOR": "WELL_ESTABLISHED",
    "ARB": "WELL_ESTABLISHED",
    "POTASSIUM_SPARING_DIURETIC": "WELL_ESTABLISHED",
    "NSAID": "WELL_ESTABLISHED",
    "NEPHROTOXIC_ANTIBIOTIC": "WELL_ESTABLISHED",
    "AMINOGLYCOSIDE": "WELL_ESTABLISHED",
    "CALCINEURIN_INHIBITOR": "WELL_ESTABLISHED",
    "CORTICOSTEROID": "WELL_ESTABLISHED",
    "ATYPICAL_ANTIPSYCHOTIC": "MODERATE",
    "BIGUANIDE": "WELL_ESTABLISHED",
    "INSULIN": "WELL_ESTABLISHED",
}


class _IdentifiedInteraction(TypedDict):
    medication_display: str
    drug_class: str
    direction: InteractionDirection
    evidence_strength: EvidenceStrength


def _identify_interactions(
    lab_type: LabType, active_medications: list[MedicationRef]
) -> list[_IdentifiedInteraction]:
    """Walk the active medication list, classify each, return interactions for the lab type."""
    directions = _DIRECTIONS[lab_type]
    out: list[_IdentifiedInteraction] = []
    for med in active_medications:
        drug_class = med.drug_class
        if not drug_class:
            entry = lookup_drug_class(med.display)
            if entry is None:
                continue
            drug_class = entry["drug_class"]
        # Confirm the class is in the lookup table and affects this lab
        canonical = next(
            (e for e in DRUG_CLASS_LOOKUP.values() if e["drug_class"] == drug_class), None
        )
        if canonical is None or lab_type not in canonical["affects_labs"]:
            continue
        direction = directions.get(drug_class)
        if direction is None:
            continue
        out.append(
            {
                "medication_display": med.display,
                "drug_class": drug_class,
                "direction": direction,
                "evidence_strength": _EVIDENCE_BY_CLASS.get(drug_class, "MODERATE"),
            }
        )
    return out


def _is_significant(identified: list[_IdentifiedInteraction]) -> bool:
    """Significant if any INCREASES interaction exists. DECREASES alone is informational."""
    return any(item["direction"] == "INCREASES" for item in identified)


def run(
    lab_type: LabType,
    active_medications: list[MedicationRef],
    *,
    anthropic_client: Anthropic | None = None,
) -> MedicationInteractions:
    """Two-step analysis: deterministic detection + LLM-narrated mechanisms."""
    identified = _identify_interactions(lab_type, active_medications)

    if not identified:
        return MedicationInteractions(
            interactions_found=[],
            cumulative_risk_note="No identified medication interactions for this lab type.",
            has_significant_interactions=False,
        )

    llm_response = call_interaction_llm(
        lab_type=lab_type,
        identified_interactions=[
            (item["medication_display"], item["drug_class"], item["direction"])
            for item in identified
        ],
        client=anthropic_client,
    )

    # Merge mechanism narration back into the structured findings, matching by name
    summary_by_med = {entry.medication: entry.summary for entry in llm_response.mechanisms}
    interactions: list[MedicationInteraction] = []
    for item in identified:
        summary = summary_by_med.get(item["medication_display"], "Mechanism not well established")
        interactions.append(
            MedicationInteraction(
                medication_display=item["medication_display"],
                drug_class=item["drug_class"],
                direction=item["direction"],
                mechanism_summary=summary,
                evidence_strength=item["evidence_strength"],
            )
        )

    return MedicationInteractions(
        interactions_found=interactions,
        cumulative_risk_note=llm_response.cumulative_risk_note,
        has_significant_interactions=_is_significant(identified),
    )
