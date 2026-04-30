"""High-level FHIR queries that parse Bundle responses into LabLens Pydantic models.

These functions are permissive on input shape: FHIR servers vary slightly in
how they encode optional fields, and we'd rather degrade gracefully than crash
the demo. Missing fields become `None` or empty lists.
"""

from __future__ import annotations

from datetime import date, timedelta
from statistics import median
from typing import Any

import httpx

from lablens.clinical.drug_classes import lookup_drug_class
from lablens.clinical.lab_loinc_codes import LAB_DISPLAY, LAB_UNIT, LOINC_BY_LAB_TYPE, LabType
from lablens.clinical.models import (
    AllergyRef,
    ConditionRef,
    Demographics,
    EncounterRef,
    LabTrendResult,
    LabValuePoint,
    MedicationRef,
    PatientContext,
    Trend,
)
from lablens.fhir.client import FhirClient


def _bundle_entries(bundle: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not bundle:
        return []
    entries = bundle.get("entry") or []
    return [e.get("resource", {}) for e in entries if isinstance(e, dict)]


def _coding_display_and_code(codeable_concept: dict[str, Any] | None) -> tuple[str, str]:
    if not codeable_concept:
        return ("", "")
    text = codeable_concept.get("text") or ""
    coding = codeable_concept.get("coding") or []
    if coding:
        first = coding[0]
        return (text or first.get("display") or "", first.get("code") or "")
    return (text, "")


def _parse_demographics(patient: dict[str, Any] | None) -> Demographics:
    if not patient:
        return Demographics(age=0, sex="unknown")
    sex = patient.get("gender") or "unknown"
    birth_date = patient.get("birthDate")
    age = 0
    if birth_date:
        try:
            born = date.fromisoformat(birth_date)
            today = date.today()
            age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        except ValueError:
            age = 0
    return Demographics(age=age, sex=sex)


def _parse_conditions(bundle: dict[str, Any] | None) -> list[ConditionRef]:
    out: list[ConditionRef] = []
    for resource in _bundle_entries(bundle):
        display, code = _coding_display_and_code(resource.get("code"))
        out.append(
            ConditionRef(
                code=code,
                display=display,
                onset_date=resource.get("onsetDateTime"),
            )
        )
    return out


def _parse_medication_resource(resource: dict[str, Any]) -> MedicationRef:
    """Handle both MedicationRequest and MedicationStatement shapes — they overlap."""
    medication_cc = resource.get("medicationCodeableConcept") or resource.get("medication", {}).get(
        "concept"
    )
    display, code = _coding_display_and_code(medication_cc)
    dose: str | None = None
    frequency: str | None = None
    instructions = resource.get("dosageInstruction") or resource.get("dosage") or []
    if instructions:
        first = instructions[0]
        if isinstance(first, dict):
            dose = first.get("text")
            timing = first.get("timing", {}) if isinstance(first.get("timing"), dict) else {}
            repeat = timing.get("repeat", {}) if isinstance(timing.get("repeat"), dict) else {}
            freq = repeat.get("frequency")
            period = repeat.get("period")
            period_unit = repeat.get("periodUnit")
            if freq is not None and period is not None and period_unit:
                frequency = f"{freq} per {period} {period_unit}"
    drug_class = None
    if display:
        entry = lookup_drug_class(display)
        if entry:
            drug_class = entry["drug_class"]
    return MedicationRef(
        code=code,
        display=display,
        dose=dose,
        frequency=frequency,
        drug_class=drug_class,
    )


def _parse_medications(bundle: dict[str, Any] | None) -> list[MedicationRef]:
    return [_parse_medication_resource(r) for r in _bundle_entries(bundle)]


def _dedupe_medications(meds: list[MedicationRef]) -> list[MedicationRef]:
    """Same drug may appear in both MedicationRequest and MedicationStatement bundles.
    Deduplicate by display+code, keeping the first occurrence (which has dose info).
    """
    seen: set[tuple[str, str]] = set()
    out: list[MedicationRef] = []
    for med in meds:
        key = (med.display.lower(), med.code)
        if key in seen:
            continue
        seen.add(key)
        out.append(med)
    return out


def _parse_allergies(bundle: dict[str, Any] | None) -> list[AllergyRef]:
    out: list[AllergyRef] = []
    for resource in _bundle_entries(bundle):
        substance, _ = _coding_display_and_code(resource.get("code"))
        reactions = resource.get("reaction") or []
        reaction_text: str | None = None
        if reactions and isinstance(reactions[0], dict):
            manifestations = reactions[0].get("manifestation") or []
            if manifestations and isinstance(manifestations[0], dict):
                reaction_text = (
                    manifestations[0].get("text") or _coding_display_and_code(manifestations[0])[0]
                )
        out.append(
            AllergyRef(
                substance=substance,
                reaction=reaction_text,
                severity=resource.get("criticality"),
            )
        )
    return out


def _parse_encounters(bundle: dict[str, Any] | None) -> list[EncounterRef]:
    out: list[EncounterRef] = []
    for resource in _bundle_entries(bundle):
        period = resource.get("period") or {}
        date_value = period.get("start") or resource.get("date") or ""
        type_list = resource.get("type") or []
        type_text = ""
        if type_list and isinstance(type_list[0], dict):
            type_text, _ = _coding_display_and_code(type_list[0])
        if not type_text:
            type_text = resource.get("class", {}).get("display") or "encounter"
        reason_list = resource.get("reasonCode") or []
        reason: str | None = None
        if reason_list and isinstance(reason_list[0], dict):
            reason, _ = _coding_display_and_code(reason_list[0])
        out.append(EncounterRef(date=str(date_value), type=type_text, reason=reason))
    return out


def _six_months_ago_iso() -> str:
    return (date.today() - timedelta(days=6 * 30)).isoformat()


async def fetch_patient_context(client: FhirClient, patient_id: str) -> PatientContext:
    """Pull active conditions, meds, allergies, recent encounters for a patient.

    Queries both MedicationRequest and MedicationStatement and merges the results
    (deduplicated). Different FHIR servers / synthetic data sources put active meds
    in different resource types, so we look in both.
    """

    async def _safe_search(resource_type: str, params: dict[str, str]) -> dict[str, Any] | None:
        """Some FHIR servers reject queries on resources they don't expose (403/404).
        Treat those as "no data" rather than crashing the whole tool call.
        """
        try:
            return await client.search(resource_type, params)
        except httpx.HTTPStatusError:
            return None

    patient = await client.read(f"Patient/{patient_id}")
    conditions_bundle = await _safe_search(
        "Condition", {"patient": patient_id, "clinical-status": "active"}
    )
    med_request_bundle = await _safe_search(
        "MedicationRequest", {"patient": patient_id, "status": "active"}
    )
    med_statement_bundle = await _safe_search(
        "MedicationStatement", {"patient": patient_id, "status": "active"}
    )
    allergies_bundle = await _safe_search("AllergyIntolerance", {"patient": patient_id})
    encounters_bundle = await _safe_search(
        "Encounter", {"patient": patient_id, "date": f"ge{_six_months_ago_iso()}"}
    )
    merged_meds = _dedupe_medications(
        _parse_medications(med_request_bundle) + _parse_medications(med_statement_bundle)
    )
    return PatientContext(
        patient_id=patient_id,
        demographics=_parse_demographics(patient),
        active_conditions=_parse_conditions(conditions_bundle),
        active_medications=merged_meds,
        allergies=_parse_allergies(allergies_bundle),
        recent_encounters=_parse_encounters(encounters_bundle),
    )


def _parse_observation_value(
    resource: dict[str, Any],
) -> tuple[float, str, float | None, float | None] | None:
    qty = resource.get("valueQuantity")
    if not qty or qty.get("value") is None:
        return None
    value = float(qty["value"])
    effective = (
        resource.get("effectiveDateTime") or resource.get("issued") or resource.get("date") or ""
    )
    ref_low: float | None = None
    ref_high: float | None = None
    references = resource.get("referenceRange") or []
    if references and isinstance(references[0], dict):
        rng = references[0]
        low_q = rng.get("low") or {}
        high_q = rng.get("high") or {}
        low_value = low_q.get("value")
        high_value = high_q.get("value")
        if low_value is not None:
            ref_low = float(low_value)
        if high_value is not None:
            ref_high = float(high_value)
    return (value, str(effective), ref_low, ref_high)


def _compute_trend(values: list[LabValuePoint]) -> tuple[Trend, float | None]:
    """Trend logic per CLAUDE.md §6.2 — compare most recent to median of prior 3.

    INSUFFICIENT_DATA if fewer than 2 prior values. RISING / FALLING if delta > 10%
    of the prior median. STABLE otherwise.
    """
    if len(values) < 3:
        return ("INSUFFICIENT_DATA", None)
    most_recent = values[0].value
    prior = [v.value for v in values[1:4]]
    if len(prior) < 2:
        return ("INSUFFICIENT_DATA", None)
    baseline = median(prior)
    if baseline == 0:
        return ("STABLE", 0.0)
    delta = most_recent - baseline
    pct = delta / baseline
    if pct > 0.10:
        return ("RISING", round(delta, 4))
    if pct < -0.10:
        return ("FALLING", round(delta, 4))
    return ("STABLE", round(delta, 4))


async def fetch_lab_trend(
    client: FhirClient,
    patient_id: str,
    lab_type: LabType,
    lookback_months: int = 12,
) -> LabTrendResult:
    """Fetch recent observations for a lab type and compute a coarse trend."""
    loinc = LOINC_BY_LAB_TYPE[lab_type]
    earliest = (date.today() - timedelta(days=lookback_months * 30)).isoformat()
    bundle = await client.search(
        "Observation",
        {
            "patient": patient_id,
            "code": loinc,
            "_sort": "-date",
            "date": f"ge{earliest}",
            "_count": "20",
        },
    )
    points: list[LabValuePoint] = []
    for resource in _bundle_entries(bundle):
        parsed = _parse_observation_value(resource)
        if parsed is None:
            continue
        value, effective_date, ref_low, ref_high = parsed
        points.append(
            LabValuePoint(
                value=value,
                effective_date=effective_date,
                reference_low=ref_low,
                reference_high=ref_high,
            )
        )
    points.sort(key=lambda p: p.effective_date, reverse=True)
    trend, delta = _compute_trend(points)
    return LabTrendResult(
        lab_code=loinc,
        lab_display=LAB_DISPLAY[lab_type],
        unit=LAB_UNIT[lab_type],
        values=points,
        trend=trend,
        delta_from_baseline=delta,
    )
