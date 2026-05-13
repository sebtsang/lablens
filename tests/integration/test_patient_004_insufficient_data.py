"""End-to-end integration test for Patient 4 (INSUFFICIENT_DATA fail-safe)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from lablens.fhir.client import FhirClient
from lablens.fhir.queries import fetch_lab_trend, fetch_patient_context
from lablens.tools.analyze_medication_lab_interactions import run as analyze
from lablens.tools.classify_lab_followup_urgency import classify
from tests.fixtures.fake_fhir_client import FakeFhirClient

BUNDLE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "synthetic_patients"
    / "patient_004_insufficient_data.json"
)
PATIENT_ID = "lablens-patient-004"


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
async def test_patient_004_potassium_borderline_fails_safe() -> None:
    reads, searches = _split_bundle(BUNDLE_PATH, PATIENT_ID)
    fhir = cast("FhirClient", FakeFhirClient(reads=reads, searches=searches))

    patient_context = await fetch_patient_context(fhir, PATIENT_ID)
    assert patient_context.active_conditions == []
    assert patient_context.active_medications == []

    lab_trend = await fetch_lab_trend(fhir, PATIENT_ID, "POTASSIUM")
    assert lab_trend.values[0].value == 5.3
    assert lab_trend.trend == "INSUFFICIENT_DATA"

    interactions = analyze("POTASSIUM", patient_context.active_medications)
    assert interactions.has_significant_interactions is False
    assert interactions.interactions_found == []

    result = classify(
        lab_type="POTASSIUM",
        current_value=5.3,
        unit="mmol/L",
        patient_context=patient_context,
        lab_trend=lab_trend,
        medication_interactions=interactions,
    )
    assert result.urgency == "INSUFFICIENT_DATA"
    assert any("borderline" in t.lower() for t in result.rule_trace)
    assert any("INSUFFICIENT_DATA" in t for t in result.rule_trace)
