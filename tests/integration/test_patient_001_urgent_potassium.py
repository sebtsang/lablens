"""End-to-end integration test for Patient 1 (K+ wow case, CLAUDE.md §10).

Loads the FHIR transaction Bundle for Patient 1, splits it back into the per-resource
search responses our tools expect, runs the full pipeline (get_patient_context →
get_lab_trend → analyze_medication_lab_interactions → classify), and asserts the
expected URGENT outcome with the medication-driven rule trace.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
from anthropic import Anthropic

from lablens.fhir.client import FhirClient
from lablens.fhir.queries import fetch_lab_trend, fetch_patient_context
from lablens.tools.analyze_medication_lab_interactions import run as analyze
from lablens.tools.classify_lab_followup_urgency import classify
from tests.fixtures.fake_anthropic import FakeAnthropic
from tests.fixtures.fake_fhir_client import FakeFhirClient

BUNDLE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "synthetic_patients"
    / "patient_001_urgent_potassium.json"
)

PATIENT_ID = "lablens-patient-001"

LLM_RESPONSE_FOR_PATIENT_1 = json.dumps(
    {
        "mechanisms": [
            {
                "medication": "Lisinopril 20 mg oral tablet",
                "summary": "ACE inhibition reduces aldosterone, decreasing renal potassium excretion.",
            },
            {
                "medication": "Spironolactone 25 mg oral tablet",
                "summary": "Aldosterone receptor antagonism in the distal tubule directly retains potassium.",
            },
            {
                "medication": "Ibuprofen 400 mg oral tablet",
                "summary": "NSAID prostaglandin inhibition reduces renal blood flow and potassium excretion.",
            },
        ],
        "cumulative_risk_note": (
            "Three independent K+-raising mechanisms (ACE inhibition, aldosterone antagonism, "
            "NSAID-mediated renal hypoperfusion) coexist in this patient's regimen, "
            "compounding hyperkalemia risk."
        ),
    }
)


def _split_bundle_into_search_responses(
    bundle_path: Path, patient_id: str
) -> tuple[
    dict[str, dict[str, Any] | None],
    dict[tuple[str, frozenset[tuple[str, str]]], dict[str, Any] | None],
]:
    """Convert a transaction bundle into per-resource lookups our FakeFhirClient expects."""
    raw = json.loads(bundle_path.read_text())
    entries: list[dict[str, Any]] = raw.get("entry", [])

    by_type: dict[str, list[dict[str, Any]]] = {}
    patient_resource: dict[str, Any] | None = None
    for entry in entries:
        resource = entry.get("resource", {})
        rt = resource.get("resourceType")
        if rt == "Patient":
            patient_resource = resource
        else:
            by_type.setdefault(rt, []).append(resource)

    reads: dict[str, dict[str, Any] | None] = {f"Patient/{patient_id}": patient_resource}

    def bundle_of(resources: list[dict[str, Any]]) -> dict[str, Any] | None:
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [{"resource": r} for r in resources],
        }

    searches: dict[tuple[str, frozenset[tuple[str, str]]], dict[str, Any] | None] = {
        ("Condition", frozenset()): bundle_of(by_type.get("Condition", [])),
        ("MedicationRequest", frozenset()): bundle_of(by_type.get("MedicationRequest", [])),
        ("AllergyIntolerance", frozenset()): bundle_of(by_type.get("AllergyIntolerance", [])),
        ("Encounter", frozenset()): bundle_of(by_type.get("Encounter", [])),
        ("Observation", frozenset()): bundle_of(by_type.get("Observation", [])),
    }
    return reads, searches


@pytest.mark.asyncio
async def test_patient_001_urgent_potassium_full_pipeline() -> None:
    reads, searches = _split_bundle_into_search_responses(BUNDLE_PATH, PATIENT_ID)
    fake_fhir = cast("FhirClient", FakeFhirClient(reads=reads, searches=searches))
    fake_anthropic = cast("Anthropic", FakeAnthropic(LLM_RESPONSE_FOR_PATIENT_1))

    # Step 1: pull patient context
    patient_context = await fetch_patient_context(fake_fhir, PATIENT_ID)
    assert patient_context.demographics.age >= 65
    assert len(patient_context.active_conditions) == 3
    assert {c.display for c in patient_context.active_conditions} >= {
        "Chronic kidney disease stage 3b",
        "Heart failure with reduced ejection fraction",
    }
    assert len(patient_context.active_medications) == 4
    drug_classes = {m.drug_class for m in patient_context.active_medications}
    # Furosemide isn't in our table — its class will be None, which is fine
    assert {"ACE_INHIBITOR", "POTASSIUM_SPARING_DIURETIC", "NSAID"}.issubset(drug_classes)

    # Step 2: pull K+ trend
    lab_trend = await fetch_lab_trend(fake_fhir, PATIENT_ID, "POTASSIUM")
    assert lab_trend.trend == "RISING"
    assert lab_trend.values[0].value == 6.1

    # Step 3: medication-interaction analysis (with mocked LLM)
    interactions = analyze(
        "POTASSIUM",
        patient_context.active_medications,
        anthropic_client=fake_anthropic,
    )
    assert interactions.has_significant_interactions is True
    assert len(interactions.interactions_found) == 3
    classes_found = {i.drug_class for i in interactions.interactions_found}
    assert classes_found == {"ACE_INHIBITOR", "POTASSIUM_SPARING_DIURETIC", "NSAID"}
    assert "Three independent" in interactions.cumulative_risk_note

    # Step 4: classify urgency
    result = classify(
        lab_type="POTASSIUM",
        current_value=6.1,
        unit="mmol/L",
        patient_context=patient_context,
        lab_trend=lab_trend,
        medication_interactions=interactions,
    )

    assert result.urgency == "URGENT"
    assert any(">= 6.0" in t for t in result.rule_trace)
    assert "4 hours" in result.recommended_review_path
    assert "Synthetic demo" in result.safety_label
