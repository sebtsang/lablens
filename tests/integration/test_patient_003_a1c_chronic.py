"""End-to-end integration test for Patient 3 (HbA1c chronic, CLAUDE.md §10)."""

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
    / "patient_003_a1c_chronic.json"
)
PATIENT_ID = "lablens-patient-003"

# Patient 3 has Metformin (DECREASES A1c) only — no A1c-INCREASING drugs. We
# expect the LLM to be called only with metformin.
LLM_RESPONSE = json.dumps(
    {
        "mechanisms": [
            {
                "medication": "Metformin 1000 mg oral tablet",
                "summary": "Reduces hepatic gluconeogenesis and increases insulin sensitivity, lowering A1c.",
            }
        ],
        "cumulative_risk_note": "A1c-lowering medication present; no A1c-raising drugs identified.",
    }
)


def _split_bundle(
    bundle_path: Path, patient_id: str
) -> tuple[
    dict[str, dict[str, Any] | None],
    dict[tuple[str, frozenset[tuple[str, str]]], dict[str, Any] | None],
]:
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

    def bundle_of(resources: list[dict[str, Any]]) -> dict[str, Any] | None:
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [{"resource": r} for r in resources],
        }

    reads: dict[str, dict[str, Any] | None] = {f"Patient/{patient_id}": patient_resource}
    searches: dict[tuple[str, frozenset[tuple[str, str]]], dict[str, Any] | None] = {
        ("Condition", frozenset()): bundle_of(by_type.get("Condition", [])),
        ("MedicationRequest", frozenset()): bundle_of(by_type.get("MedicationRequest", [])),
        ("AllergyIntolerance", frozenset()): bundle_of(by_type.get("AllergyIntolerance", [])),
        ("Encounter", frozenset()): bundle_of(by_type.get("Encounter", [])),
        ("Observation", frozenset()): bundle_of(by_type.get("Observation", [])),
    }
    return reads, searches


@pytest.mark.asyncio
async def test_patient_003_a1c_chronic_full_pipeline() -> None:
    reads, searches = _split_bundle(BUNDLE_PATH, PATIENT_ID)
    fhir = cast("FhirClient", FakeFhirClient(reads=reads, searches=searches))
    anth = cast("Anthropic", FakeAnthropic(LLM_RESPONSE))

    patient_context = await fetch_patient_context(fhir, PATIENT_ID)
    diabetes = any("diabetes" in c.display.lower() for c in patient_context.active_conditions)
    assert diabetes

    lab_trend = await fetch_lab_trend(fhir, PATIENT_ID, "HBA1C")
    assert lab_trend.values[0].value == 9.8
    assert lab_trend.trend in ("RISING", "STABLE")  # 9.8 / median(9.2, 8.8, 8.5) ~ +9% — STABLE

    interactions = analyze("HBA1C", patient_context.active_medications, anthropic_client=anth)
    # Metformin is DECREASES — informational, not significant
    assert len(interactions.interactions_found) == 1
    assert interactions.interactions_found[0].direction == "DECREASES"
    assert interactions.has_significant_interactions is False

    result = classify(
        lab_type="HBA1C",
        current_value=9.8,
        unit="%",
        patient_context=patient_context,
        lab_trend=lab_trend,
        medication_interactions=interactions,
    )
    # §9: HbA1c never escalates to URGENT, even at 9.8
    assert result.urgency == "SOON"
    assert "1-2 business days" in result.recommended_review_path
