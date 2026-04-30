"""Shared pytest fixtures for LabLens tests."""

from __future__ import annotations

import pytest

from lablens.clinical.models import (
    Demographics,
    LabTrendResult,
    MedicationInteractions,
    PatientContext,
)


@pytest.fixture
def empty_patient() -> PatientContext:
    return PatientContext(
        patient_id="p-empty",
        demographics=Demographics(age=50, sex="unknown"),
    )


@pytest.fixture
def diabetic_patient() -> PatientContext:
    return PatientContext(
        patient_id="p-dm",
        demographics=Demographics(age=55, sex="male"),
    )


def make_trend(
    *,
    trend: str = "STABLE",
    delta: float | None = None,
    lab_code: str = "2823-3",
    unit: str = "mmol/L",
) -> LabTrendResult:
    return LabTrendResult(
        lab_code=lab_code,
        lab_display="test lab",
        unit=unit,
        values=[],
        trend=trend,  # type: ignore[arg-type]
        delta_from_baseline=delta,
    )


def make_meds(*, has_interactions: bool = False) -> MedicationInteractions:
    return MedicationInteractions(
        interactions_found=[],
        cumulative_risk_note="(test fixture)",
        has_significant_interactions=has_interactions,
    )


@pytest.fixture
def no_trend() -> LabTrendResult:
    return make_trend(trend="INSUFFICIENT_DATA")


@pytest.fixture
def stable_trend() -> LabTrendResult:
    return make_trend(trend="STABLE")


@pytest.fixture
def rising_trend_potassium() -> LabTrendResult:
    return make_trend(trend="RISING", delta=0.6)


@pytest.fixture
def rising_trend_creatinine() -> LabTrendResult:
    return make_trend(trend="RISING", delta=0.5, lab_code="2160-0", unit="mg/dL")


@pytest.fixture
def no_meds() -> MedicationInteractions:
    return make_meds(has_interactions=False)


@pytest.fixture
def med_interactions() -> MedicationInteractions:
    return make_meds(has_interactions=True)
