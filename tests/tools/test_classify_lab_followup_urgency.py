"""Unit tests for classify_lab_followup_urgency — every rule branch in CLAUDE.md §9."""

from __future__ import annotations

import pytest

from lablens.clinical.models import (
    ConditionRef,
    Demographics,
    LabTrendResult,
    MedicationInteractions,
    PatientContext,
)
from lablens.clinical.safety_disclaimers import SAFETY_LABEL
from lablens.tools.classify_lab_followup_urgency import classify

# ---------------------------------------------------------------------------
# POTASSIUM rule branches (CLAUDE.md §9)
# ---------------------------------------------------------------------------


def test_potassium_severe_hyperkalemia_is_urgent(
    empty_patient: PatientContext,
    no_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("POTASSIUM", 6.1, "mmol/L", empty_patient, no_trend, no_meds)
    assert result.urgency == "URGENT"
    assert any(">= 6.0" in t for t in result.rule_trace)


def test_potassium_5_5_with_rising_trend_escalates_to_urgent(
    empty_patient: PatientContext,
    rising_trend_potassium: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("POTASSIUM", 5.6, "mmol/L", empty_patient, rising_trend_potassium, no_meds)
    assert result.urgency == "URGENT"
    assert any("RISING trend" in t for t in result.rule_trace)


def test_potassium_5_5_with_med_interactions_escalates_to_urgent(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    med_interactions: MedicationInteractions,
) -> None:
    result = classify("POTASSIUM", 5.7, "mmol/L", empty_patient, stable_trend, med_interactions)
    assert result.urgency == "URGENT"
    assert any("medications" in t for t in result.rule_trace)


def test_potassium_5_5_with_no_signals_is_soon(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("POTASSIUM", 5.6, "mmol/L", empty_patient, stable_trend, no_meds)
    assert result.urgency == "SOON"


def test_potassium_5_0_with_med_interactions_escalates_to_soon(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    med_interactions: MedicationInteractions,
) -> None:
    result = classify("POTASSIUM", 5.1, "mmol/L", empty_patient, stable_trend, med_interactions)
    assert result.urgency == "SOON"


def test_potassium_5_0_no_signals_is_routine(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("POTASSIUM", 5.1, "mmol/L", empty_patient, stable_trend, no_meds)
    assert result.urgency == "ROUTINE"


def test_potassium_hypokalemia_is_soon(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("POTASSIUM", 3.2, "mmol/L", empty_patient, stable_trend, no_meds)
    assert result.urgency == "SOON"
    assert any("hypokalemia" in t.lower() for t in result.rule_trace)


def test_potassium_normal_value_is_routine(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("POTASSIUM", 4.2, "mmol/L", empty_patient, stable_trend, no_meds)
    assert result.urgency == "ROUTINE"


# ---------------------------------------------------------------------------
# CREATININE rule branches
# ---------------------------------------------------------------------------


def test_creatinine_above_2_with_rising_trend_is_urgent(
    empty_patient: PatientContext,
    rising_trend_creatinine: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("CREATININE", 2.1, "mg/dL", empty_patient, rising_trend_creatinine, no_meds)
    assert result.urgency == "URGENT"


def test_creatinine_large_delta_from_baseline_is_urgent(
    empty_patient: PatientContext,
    no_meds: MedicationInteractions,
) -> None:
    trend = LabTrendResult(
        lab_code="2160-0",
        lab_display="Creatinine",
        unit="mg/dL",
        values=[],
        trend="STABLE",
        delta_from_baseline=0.7,
    )
    result = classify("CREATININE", 1.8, "mg/dL", empty_patient, trend, no_meds)
    assert result.urgency == "URGENT"
    assert any("delta" in t.lower() for t in result.rule_trace)


def test_creatinine_above_1_5_with_med_interactions_is_soon(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    med_interactions: MedicationInteractions,
) -> None:
    trend = LabTrendResult(
        lab_code="2160-0",
        lab_display="Creatinine",
        unit="mg/dL",
        values=[],
        trend="STABLE",
        delta_from_baseline=0.1,
    )
    result = classify("CREATININE", 1.7, "mg/dL", empty_patient, trend, med_interactions)
    assert result.urgency == "SOON"


def test_creatinine_above_1_5_no_signals_is_soon(
    empty_patient: PatientContext,
    no_meds: MedicationInteractions,
) -> None:
    trend = LabTrendResult(
        lab_code="2160-0",
        lab_display="Creatinine",
        unit="mg/dL",
        values=[],
        trend="STABLE",
        delta_from_baseline=0.0,
    )
    result = classify("CREATININE", 1.7, "mg/dL", empty_patient, trend, no_meds)
    assert result.urgency == "SOON"


def test_creatinine_rising_with_moderate_delta_is_soon(
    empty_patient: PatientContext,
    no_meds: MedicationInteractions,
) -> None:
    trend = LabTrendResult(
        lab_code="2160-0",
        lab_display="Creatinine",
        unit="mg/dL",
        values=[],
        trend="RISING",
        delta_from_baseline=0.35,
    )
    result = classify("CREATININE", 1.3, "mg/dL", empty_patient, trend, no_meds)
    assert result.urgency == "SOON"


def test_creatinine_normal_is_routine(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    trend = LabTrendResult(
        lab_code="2160-0",
        lab_display="Creatinine",
        unit="mg/dL",
        values=[],
        trend="STABLE",
        delta_from_baseline=0.0,
    )
    result = classify("CREATININE", 1.0, "mg/dL", empty_patient, trend, no_meds)
    assert result.urgency == "ROUTINE"


# ---------------------------------------------------------------------------
# HBA1C rule branches
# ---------------------------------------------------------------------------


def _diabetic_patient() -> PatientContext:
    return PatientContext(
        patient_id="p-dm",
        demographics=Demographics(age=55, sex="male"),
        active_conditions=[
            ConditionRef(
                code="44054006", display="Type 2 diabetes mellitus", onset_date="2018-01-01"
            ),
        ],
    )


def test_hba1c_severely_uncontrolled_is_soon_not_urgent(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("HBA1C", 11.0, "%", empty_patient, stable_trend, no_meds)
    # §9 footnote: HbA1c never escalates to URGENT in this demo
    assert result.urgency == "SOON"


def test_hba1c_above_9_is_soon(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("HBA1C", 9.5, "%", empty_patient, stable_trend, no_meds)
    assert result.urgency == "SOON"


def test_hba1c_above_7_with_diabetes_is_routine(
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    patient = _diabetic_patient()
    result = classify("HBA1C", 7.5, "%", patient, stable_trend, no_meds)
    assert result.urgency == "ROUTINE"
    assert any("scheduled" in t.lower() for t in result.rule_trace)


def test_hba1c_above_6_5_without_diabetes_is_soon(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("HBA1C", 6.7, "%", empty_patient, stable_trend, no_meds)
    assert result.urgency == "SOON"
    assert any("new" in t.lower() and "diagnosis" in t.lower() for t in result.rule_trace)


def test_hba1c_normal_is_routine(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("HBA1C", 5.4, "%", empty_patient, stable_trend, no_meds)
    assert result.urgency == "ROUTINE"


# ---------------------------------------------------------------------------
# INSUFFICIENT_DATA fail-safe (CLAUDE.md §6.4)
# ---------------------------------------------------------------------------


def test_potassium_borderline_with_no_signals_returns_insufficient_data(
    empty_patient: PatientContext,
    no_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("POTASSIUM", 5.3, "mmol/L", empty_patient, no_trend, no_meds)
    assert result.urgency == "INSUFFICIENT_DATA"
    assert any("borderline" in t.lower() for t in result.rule_trace)


def test_borderline_value_with_med_signal_does_not_trip_failsafe(
    empty_patient: PatientContext,
    no_trend: LabTrendResult,
    med_interactions: MedicationInteractions,
) -> None:
    # Same borderline value as above but with med interactions — should classify, not bail
    result = classify("POTASSIUM", 5.3, "mmol/L", empty_patient, no_trend, med_interactions)
    assert result.urgency != "INSUFFICIENT_DATA"


# ---------------------------------------------------------------------------
# Output packet contract checks
# ---------------------------------------------------------------------------


def test_safety_label_present_in_every_output(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("POTASSIUM", 4.0, "mmol/L", empty_patient, stable_trend, no_meds)
    assert result.safety_label == SAFETY_LABEL
    assert "Synthetic demo" in result.safety_label


def test_recommended_review_path_matches_urgency(
    empty_patient: PatientContext,
    no_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    urgent = classify(
        "POTASSIUM", 6.5, "mmol/L", empty_patient, no_trend, no_meds
    ).recommended_review_path
    soon = classify(
        "POTASSIUM", 3.0, "mmol/L", empty_patient, no_trend, no_meds
    ).recommended_review_path
    routine = classify(
        "POTASSIUM", 4.0, "mmol/L", empty_patient, no_trend, no_meds
    ).recommended_review_path
    assert "4 hours" in urgent
    assert "1-2 business days" in soon
    assert "next scheduled visit" in routine


def test_unit_mismatch_added_to_trace_but_does_not_fail(
    empty_patient: PatientContext,
    stable_trend: LabTrendResult,
    no_meds: MedicationInteractions,
) -> None:
    result = classify("POTASSIUM", 4.2, "mEq/L", empty_patient, stable_trend, no_meds)
    assert any("differs from expected" in t for t in result.rule_trace)
    assert result.urgency == "ROUTINE"


# ---------------------------------------------------------------------------
# Determinism check
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("_iteration", range(20))
def test_classifier_is_deterministic(
    _iteration: int,
    empty_patient: PatientContext,
    rising_trend_potassium: LabTrendResult,
    med_interactions: MedicationInteractions,
) -> None:
    a = classify(
        "POTASSIUM", 5.7, "mmol/L", empty_patient, rising_trend_potassium, med_interactions
    )
    b = classify(
        "POTASSIUM", 5.7, "mmol/L", empty_patient, rising_trend_potassium, med_interactions
    )
    assert a.model_dump() == b.model_dump()
