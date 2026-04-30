"""Tests for fetch_patient_context — parsing FHIR Bundles into PatientContext."""

from __future__ import annotations

from typing import cast

import pytest

from lablens.fhir.client import FhirClient
from lablens.fhir.queries import fetch_patient_context
from tests.fixtures.fake_fhir_client import FakeFhirClient
from tests.fixtures.fhir_fixtures import (
    allergies_bundle,
    conditions_bundle,
    empty_bundle,
    encounters_bundle,
    medications_bundle,
    patient_resource,
)


@pytest.mark.asyncio
async def test_returns_patient_with_demographics_and_active_meds_with_drug_classes() -> None:
    fake = FakeFhirClient(
        reads={"Patient/p-001": patient_resource(patient_id="p-001", birth_date="1958-03-14")},
        searches={
            (
                "Condition",
                frozenset({"patient": "p-001", "clinical-status": "active"}.items()),
            ): conditions_bundle([("44054006", "Type 2 diabetes mellitus")]),
            (
                "MedicationRequest",
                frozenset({"patient": "p-001", "status": "active"}.items()),
            ): medications_bundle(
                [
                    ("314076", "Lisinopril 20 mg oral tablet", "20 mg daily"),
                    ("197361", "Spironolactone 25 mg", "25 mg daily"),
                ]
            ),
            ("AllergyIntolerance", frozenset({"patient": "p-001"}.items())): allergies_bundle(
                [("Penicillin G", "Hives")]
            ),
            ("Encounter", frozenset()): encounters_bundle(
                [("2026-03-15", "Office visit", "Hypertension follow-up")]
            ),
        },
    )
    client = cast("FhirClient", fake)
    ctx = await fetch_patient_context(client, "p-001")

    assert ctx.patient_id == "p-001"
    assert ctx.demographics.sex == "female"
    assert ctx.demographics.age >= 65  # born 1958, today 2026
    assert len(ctx.active_conditions) == 1
    assert ctx.active_conditions[0].display == "Type 2 diabetes mellitus"
    assert len(ctx.active_medications) == 2
    assert ctx.active_medications[0].drug_class == "ACE_INHIBITOR"
    assert ctx.active_medications[1].drug_class == "POTASSIUM_SPARING_DIURETIC"
    assert len(ctx.allergies) == 1
    assert ctx.allergies[0].substance == "Penicillin G"
    assert len(ctx.recent_encounters) == 1


@pytest.mark.asyncio
async def test_handles_empty_bundles_gracefully() -> None:
    fake = FakeFhirClient(
        reads={"Patient/p-002": patient_resource(patient_id="p-002")},
        searches={
            ("Condition", frozenset()): empty_bundle(),
            ("MedicationRequest", frozenset()): empty_bundle(),
            ("AllergyIntolerance", frozenset()): empty_bundle(),
            ("Encounter", frozenset()): empty_bundle(),
        },
    )
    client = cast("FhirClient", fake)
    ctx = await fetch_patient_context(client, "p-002")
    assert ctx.active_conditions == []
    assert ctx.active_medications == []
    assert ctx.allergies == []
    assert ctx.recent_encounters == []


@pytest.mark.asyncio
async def test_unknown_medication_has_no_drug_class() -> None:
    fake = FakeFhirClient(
        reads={"Patient/p-003": patient_resource(patient_id="p-003")},
        searches={
            ("MedicationRequest", frozenset()): medications_bundle(
                [("123", "Acetaminophen 500 mg", "500 mg q6h")]
            ),
            ("Condition", frozenset()): empty_bundle(),
            ("AllergyIntolerance", frozenset()): empty_bundle(),
            ("Encounter", frozenset()): empty_bundle(),
        },
    )
    client = cast("FhirClient", fake)
    ctx = await fetch_patient_context(client, "p-003")
    assert len(ctx.active_medications) == 1
    assert ctx.active_medications[0].drug_class is None


@pytest.mark.asyncio
async def test_missing_patient_resource_yields_zero_age() -> None:
    fake = FakeFhirClient(
        reads={},  # Patient/{id} returns None
        searches={
            ("Condition", frozenset()): empty_bundle(),
            ("MedicationRequest", frozenset()): empty_bundle(),
            ("AllergyIntolerance", frozenset()): empty_bundle(),
            ("Encounter", frozenset()): empty_bundle(),
        },
    )
    client = cast("FhirClient", fake)
    ctx = await fetch_patient_context(client, "p-missing")
    assert ctx.demographics.age == 0
    assert ctx.demographics.sex == "unknown"
