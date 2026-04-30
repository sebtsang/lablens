"""Hand-built FHIR Bundle fixtures for parser tests.

Shapes deliberately match what HAPI / Prompt Opinion's workspace return so
parser tests catch real-world variability.
"""

from __future__ import annotations

from typing import Any


def patient_resource(
    *, patient_id: str = "p-001", birth_date: str = "1958-03-14", gender: str = "female"
) -> dict[str, Any]:
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "birthDate": birth_date,
        "gender": gender,
    }


def conditions_bundle(condition_displays: list[tuple[str, str]]) -> dict[str, Any]:
    """Each tuple is (code, display)."""
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {
                        "coding": [
                            {"system": "http://snomed.info/sct", "code": code, "display": display}
                        ],
                        "text": display,
                    },
                    "onsetDateTime": "2018-01-01",
                }
            }
            for code, display in condition_displays
        ],
    }


def medications_bundle(meds: list[tuple[str, str, str | None]]) -> dict[str, Any]:
    """Each tuple is (rxnorm_code, display, dose_text or None)."""
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "medicationCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": code,
                                "display": display,
                            }
                        ],
                        "text": display,
                    },
                    "dosageInstruction": [{"text": dose}] if dose else [],
                }
            }
            for code, display, dose in meds
        ],
    }


def allergies_bundle(allergies: list[tuple[str, str | None]]) -> dict[str, Any]:
    """Each tuple is (substance, reaction or None)."""
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            {
                "resource": {
                    "resourceType": "AllergyIntolerance",
                    "code": {"text": substance},
                    "criticality": "high" if reaction else None,
                    "reaction": ([{"manifestation": [{"text": reaction}]}] if reaction else []),
                }
            }
            for substance, reaction in allergies
        ],
    }


def encounters_bundle(encounters: list[tuple[str, str, str | None]]) -> dict[str, Any]:
    """Each tuple is (date, type_text, reason or None)."""
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            {
                "resource": {
                    "resourceType": "Encounter",
                    "period": {"start": dt},
                    "type": [{"text": type_text}],
                    "reasonCode": [{"text": reason}] if reason else [],
                }
            }
            for dt, type_text, reason in encounters
        ],
    }


def observation_bundle(values: list[tuple[float, str]], *, code: str = "2823-3") -> dict[str, Any]:
    """Each tuple is (value, effective_date_iso)."""
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": code}]},
                    "valueQuantity": {"value": value, "unit": "mmol/L"},
                    "effectiveDateTime": dt,
                    "referenceRange": [
                        {"low": {"value": 3.5}, "high": {"value": 5.0}},
                    ],
                }
            }
            for value, dt in values
        ],
    }


def empty_bundle() -> dict[str, Any]:
    return {"resourceType": "Bundle", "type": "searchset", "entry": []}
