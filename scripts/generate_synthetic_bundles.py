"""Generate FHIR transaction Bundles for our LabLens demo patients.

Output format matches what Prompt Opinion's workspace FHIR endpoint accepts —
which is the Synthea-style POST + urn:uuid: + ifNoneExist transaction shape.
The bundles are deterministic (UUIDs derived from a stable namespace) so
re-running this script produces byte-identical output.

Run:
    uv run python scripts/generate_synthetic_bundles.py

Writes:
    data/synthetic_patients/patient_001_urgent_potassium.json
    data/synthetic_patients/patient_002_creatinine_trend.json
    data/synthetic_patients/patient_003_a1c_chronic.json
    data/synthetic_patients/MANIFEST.json
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data" / "synthetic_patients"

# Stable namespace so UUIDs are deterministic
LABLENS_NAMESPACE = uuid.UUID("19af3d2c-1ab1-4c4e-a8db-11e7e7e7e001")
LABLENS_ID_SYSTEM = "https://lablens.example.org/synthea-equivalent"


def stable_uuid(seed: str) -> str:
    return str(uuid.uuid5(LABLENS_NAMESPACE, seed))


@dataclass
class CodingRef:
    system: str
    code: str
    display: str


@dataclass
class Med:
    rxnorm: str
    display: str
    dose: str


@dataclass
class Cond:
    snomed: str
    display: str
    onset: str


@dataclass
class LabObs:
    loinc: str
    loinc_display: str
    value: float
    unit: str
    effective: str
    ref_low: float
    ref_high: float


@dataclass
class PatientDef:
    short_id: str
    given: str
    family: str
    gender: str
    birth_date: str
    conditions: list[Cond] = field(default_factory=list)
    medications: list[Med] = field(default_factory=list)
    allergies: list[tuple[str, str, str]] = field(default_factory=list)  # snomed, display, reaction
    encounter_date: str = ""
    encounter_reason: str = ""
    observations: list[LabObs] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Patient 1 — K+ wow case (URGENT)
# ---------------------------------------------------------------------------
PATIENT_1 = PatientDef(
    short_id="patient-001",
    given="Patient_001_Urgent_Potassium",
    family="Demo",
    gender="female",
    birth_date="1958-03-14",
    conditions=[
        Cond("433144002", "Chronic kidney disease stage 3b", "2022-06-01"),
        Cond("59621000", "Essential hypertension", "2015-04-12"),
        Cond("703272007", "Heart failure with reduced ejection fraction", "2020-11-03"),
    ],
    medications=[
        Med("314076", "Lisinopril 20 MG Oral Tablet", "20 mg PO daily"),
        Med("313096", "Spironolactone 25 MG Oral Tablet", "25 mg PO daily"),
        Med(
            "310965",
            "Ibuprofen 400 MG Oral Tablet",
            "400 mg PO TID for back pain (started 3 weeks ago)",
        ),
        Med("313988", "Furosemide 40 MG Oral Tablet", "40 mg PO daily"),
    ],
    allergies=[("91936005", "Allergy to penicillin", "Hives")],
    encounter_date="2026-04-15",
    encounter_reason="Heart failure follow-up",
    observations=[
        LabObs(
            "2823-3",
            "Potassium [Moles/volume] in Serum or Plasma",
            6.1,
            "mmol/L",
            "2026-04-29",
            3.5,
            5.0,
        ),
        LabObs(
            "2823-3",
            "Potassium [Moles/volume] in Serum or Plasma",
            5.4,
            "mmol/L",
            "2026-04-08",
            3.5,
            5.0,
        ),
        LabObs(
            "2823-3",
            "Potassium [Moles/volume] in Serum or Plasma",
            4.8,
            "mmol/L",
            "2026-01-29",
            3.5,
            5.0,
        ),
        LabObs(
            "2823-3",
            "Potassium [Moles/volume] in Serum or Plasma",
            4.6,
            "mmol/L",
            "2025-04-29",
            3.5,
            5.0,
        ),
    ],
)

# ---------------------------------------------------------------------------
# Patient 2 — creatinine trend (URGENT)
# ---------------------------------------------------------------------------
PATIENT_2 = PatientDef(
    short_id="patient-002",
    given="Patient_002_Creatinine_Trend",
    family="Demo",
    gender="male",
    birth_date="1953-07-22",
    conditions=[
        Cond("433143008", "Chronic kidney disease stage 3a", "2023-02-15"),
        Cond("59621000", "Essential hypertension", "2014-09-01"),
        Cond("44054006", "Type 2 diabetes mellitus", "2017-05-10"),
    ],
    medications=[
        Med("979485", "Losartan 100 MG Oral Tablet", "100 mg PO daily"),
        Med("861007", "Metformin 1000 MG Oral Tablet", "1000 mg PO BID"),
        Med(
            "849574",
            "Naproxen 500 MG Oral Tablet",
            "500 mg PO BID for back pain (started 2 weeks ago)",
        ),
    ],
    encounter_date="2026-03-25",
    encounter_reason="Routine diabetes follow-up",
    observations=[
        LabObs(
            "2160-0",
            "Creatinine [Mass/volume] in Serum or Plasma",
            2.1,
            "mg/dL",
            "2026-04-29",
            0.7,
            1.3,
        ),
        LabObs(
            "2160-0",
            "Creatinine [Mass/volume] in Serum or Plasma",
            1.4,
            "mg/dL",
            "2026-03-29",
            0.7,
            1.3,
        ),
        LabObs(
            "2160-0",
            "Creatinine [Mass/volume] in Serum or Plasma",
            1.3,
            "mg/dL",
            "2025-10-29",
            0.7,
            1.3,
        ),
        LabObs(
            "2160-0",
            "Creatinine [Mass/volume] in Serum or Plasma",
            1.4,
            "mg/dL",
            "2025-04-29",
            0.7,
            1.3,
        ),
    ],
)

# ---------------------------------------------------------------------------
# Patient 3 — HbA1c chronic (SOON)
# ---------------------------------------------------------------------------
PATIENT_3 = PatientDef(
    short_id="patient-003",
    given="Patient_003_A1c_Chronic",
    family="Demo",
    gender="male",
    birth_date="1971-02-08",
    conditions=[
        Cond("44054006", "Type 2 diabetes mellitus", "2018-03-12"),
        Cond("59621000", "Essential hypertension", "2019-08-04"),
    ],
    medications=[
        Med("861007", "Metformin 1000 MG Oral Tablet", "1000 mg PO BID"),
        Med("197361", "Amlodipine 5 MG Oral Tablet", "5 mg PO daily"),
    ],
    encounter_date="2025-11-29",
    encounter_reason="Diabetes management (last seen 5 months ago, missed 3-month follow-up)",
    observations=[
        LabObs(
            "4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", 9.8, "%", "2026-04-29", 4.0, 5.6
        ),
        LabObs(
            "4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", 9.2, "%", "2025-12-29", 4.0, 5.6
        ),
        LabObs(
            "4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", 8.8, "%", "2025-06-29", 4.0, 5.6
        ),
        LabObs(
            "4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", 8.5, "%", "2024-12-29", 4.0, 5.6
        ),
    ],
)

# ---------------------------------------------------------------------------
# Patient 4 — INSUFFICIENT_DATA fail-safe (no meds, no conditions, single lab)
# ---------------------------------------------------------------------------
# Demonstrates that the agent fails safely when it lacks the context to
# stratify confidently. Single borderline K+ value (5.3), no prior values,
# no medications, no conditions. Expected: INSUFFICIENT_DATA.
PATIENT_4 = PatientDef(
    short_id="patient-004",
    given="Patient_004_Insufficient_Data",
    family="Demo",
    gender="female",
    birth_date="1981-09-22",
    conditions=[],
    medications=[],
    allergies=[],
    encounter_date="",
    encounter_reason="",
    observations=[
        LabObs(
            "2823-3",
            "Potassium [Moles/volume] in Serum or Plasma",
            5.3,
            "mmol/L",
            "2026-04-29",
            3.5,
            5.0,
        ),
    ],
)

ALL_PATIENTS = [PATIENT_1, PATIENT_2, PATIENT_3, PATIENT_4]


# ---------------------------------------------------------------------------
# Bundle assembly
# ---------------------------------------------------------------------------


def _entry(
    *,
    full_url: str,
    resource: dict[str, Any],
    resource_type: str,
    if_none_exist: str | None = None,
) -> dict[str, Any]:
    request: dict[str, Any] = {"method": "POST", "url": resource_type}
    if if_none_exist:
        request["ifNoneExist"] = if_none_exist
    return {"fullUrl": full_url, "resource": resource, "request": request}


def build_bundle(p: PatientDef) -> dict[str, Any]:
    patient_uuid = stable_uuid(f"{p.short_id}::Patient")
    patient_full_url = f"urn:uuid:{patient_uuid}"
    entries: list[dict[str, Any]] = []

    # Patient
    entries.append(
        _entry(
            full_url=patient_full_url,
            resource_type="Patient",
            if_none_exist=f"identifier={LABLENS_ID_SYSTEM}|{p.short_id}",
            resource={
                "resourceType": "Patient",
                "id": patient_uuid,
                "identifier": [{"system": LABLENS_ID_SYSTEM, "value": p.short_id}],
                "name": [{"family": p.family, "given": [p.given]}],
                "gender": p.gender,
                "birthDate": p.birth_date,
            },
        )
    )

    # Encounter (one recent)
    encounter_uuid = stable_uuid(f"{p.short_id}::Encounter::recent")
    encounter_full_url = f"urn:uuid:{encounter_uuid}"
    if p.encounter_date:
        entries.append(
            _entry(
                full_url=encounter_full_url,
                resource_type="Encounter",
                if_none_exist=f"identifier={LABLENS_ID_SYSTEM}|{p.short_id}-encounter-recent",
                resource={
                    "resourceType": "Encounter",
                    "id": encounter_uuid,
                    "identifier": [
                        {
                            "system": LABLENS_ID_SYSTEM,
                            "value": f"{p.short_id}-encounter-recent",
                        }
                    ],
                    "status": "finished",
                    "class": {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "AMB",
                        "display": "Ambulatory",
                    },
                    "type": [{"text": p.encounter_reason}],
                    "subject": {"reference": patient_full_url},
                    "period": {"start": p.encounter_date, "end": p.encounter_date},
                    "reasonCode": [{"text": p.encounter_reason}],
                },
            )
        )

    # Conditions
    for i, c in enumerate(p.conditions):
        cuid = stable_uuid(f"{p.short_id}::Condition::{i}::{c.snomed}")
        entries.append(
            _entry(
                full_url=f"urn:uuid:{cuid}",
                resource_type="Condition",
                if_none_exist=f"identifier={LABLENS_ID_SYSTEM}|{p.short_id}-cond-{i}",
                resource={
                    "resourceType": "Condition",
                    "id": cuid,
                    "identifier": [
                        {"system": LABLENS_ID_SYSTEM, "value": f"{p.short_id}-cond-{i}"}
                    ],
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": "active",
                            }
                        ]
                    },
                    "verificationStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                                "code": "confirmed",
                            }
                        ]
                    },
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": c.snomed,
                                "display": c.display,
                            }
                        ],
                        "text": c.display,
                    },
                    "subject": {"reference": patient_full_url},
                    "onsetDateTime": c.onset,
                },
            )
        )

    # MedicationRequests
    for i, m in enumerate(p.medications):
        muid = stable_uuid(f"{p.short_id}::MedicationRequest::{i}::{m.rxnorm}")
        entries.append(
            _entry(
                full_url=f"urn:uuid:{muid}",
                resource_type="MedicationRequest",
                if_none_exist=f"identifier={LABLENS_ID_SYSTEM}|{p.short_id}-med-{i}",
                resource={
                    "resourceType": "MedicationRequest",
                    "id": muid,
                    "identifier": [{"system": LABLENS_ID_SYSTEM, "value": f"{p.short_id}-med-{i}"}],
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": patient_full_url},
                    "medicationCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": m.rxnorm,
                                "display": m.display,
                            }
                        ],
                        "text": m.display,
                    },
                    "dosageInstruction": [{"text": m.dose}],
                },
            )
        )

    # AllergyIntolerance
    for i, (snomed, display, reaction) in enumerate(p.allergies):
        auid = stable_uuid(f"{p.short_id}::AllergyIntolerance::{i}::{snomed}")
        entries.append(
            _entry(
                full_url=f"urn:uuid:{auid}",
                resource_type="AllergyIntolerance",
                if_none_exist=f"identifier={LABLENS_ID_SYSTEM}|{p.short_id}-allergy-{i}",
                resource={
                    "resourceType": "AllergyIntolerance",
                    "id": auid,
                    "identifier": [
                        {"system": LABLENS_ID_SYSTEM, "value": f"{p.short_id}-allergy-{i}"}
                    ],
                    "patient": {"reference": patient_full_url},
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": snomed,
                                "display": display,
                            }
                        ],
                        "text": display,
                    },
                    "criticality": "high",
                    "reaction": [{"manifestation": [{"text": reaction}]}],
                },
            )
        )

    # Observations (each lab value point)
    for i, o in enumerate(p.observations):
        ouid = stable_uuid(f"{p.short_id}::Observation::{i}::{o.loinc}::{o.effective}")
        entries.append(
            _entry(
                full_url=f"urn:uuid:{ouid}",
                resource_type="Observation",
                if_none_exist=f"identifier={LABLENS_ID_SYSTEM}|{p.short_id}-obs-{i}",
                resource={
                    "resourceType": "Observation",
                    "id": ouid,
                    "identifier": [{"system": LABLENS_ID_SYSTEM, "value": f"{p.short_id}-obs-{i}"}],
                    "status": "final",
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": o.loinc,
                                "display": o.loinc_display,
                            }
                        ],
                        "text": o.loinc_display,
                    },
                    "subject": {"reference": patient_full_url},
                    "effectiveDateTime": o.effective,
                    "valueQuantity": {
                        "value": o.value,
                        "unit": o.unit,
                        "system": "http://unitsofmeasure.org",
                        "code": o.unit,
                    },
                    "referenceRange": [
                        {
                            "low": {"value": o.ref_low, "unit": o.unit},
                            "high": {"value": o.ref_high, "unit": o.unit},
                        }
                    ],
                },
            )
        )

    return {"resourceType": "Bundle", "type": "transaction", "entry": entries}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_patients: list[dict[str, Any]] = []

    file_map = {
        "patient-001": "patient_001_urgent_potassium.json",
        "patient-002": "patient_002_creatinine_trend.json",
        "patient-003": "patient_003_a1c_chronic.json",
        "patient-004": "patient_004_insufficient_data.json",
    }

    for p in ALL_PATIENTS:
        bundle = build_bundle(p)
        patient_uuid = stable_uuid(f"{p.short_id}::Patient")
        path = OUT_DIR / file_map[p.short_id]
        path.write_text(json.dumps(bundle, indent=2) + "\n")
        print(f"wrote {path.name} ({len(bundle['entry'])} entries, patient_uuid={patient_uuid})")
        manifest_patients.append(
            {
                "short_id": p.short_id,
                "patient_uuid": patient_uuid,
                "patient_name": f"{p.given} {p.family}",
                "bundle_file": file_map[p.short_id],
                "demographics": {
                    "gender": p.gender,
                    "birth_date": p.birth_date,
                },
                "active_medications": [m.display for m in p.medications],
                "active_conditions": [c.display for c in p.conditions],
                "lab_observations": [
                    {"loinc": o.loinc, "value": o.value, "unit": o.unit, "effective": o.effective}
                    for o in p.observations
                ],
            }
        )

    manifest = {
        "patients": manifest_patients,
        "generator": "scripts/generate_synthetic_bundles.py",
    }
    (OUT_DIR / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote MANIFEST.json ({len(manifest_patients)} patients)")


if __name__ == "__main__":
    main()
