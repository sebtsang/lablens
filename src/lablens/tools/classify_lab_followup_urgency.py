"""MCP tool: pure deterministic risk stratifier (CLAUDE.md §6.4 / §9).

Same inputs always produce same outputs. No LLM, no I/O. Implements the
INSUFFICIENT_DATA fail-safe per §6.4: if there's no trend data, no medication
interaction signal, and the value is in a borderline range, fail safe rather
than guess.
"""

from lablens.clinical.lab_loinc_codes import LAB_UNIT, LabType
from lablens.clinical.models import (
    ClassifierOutput,
    LabTrendResult,
    MedicationInteractions,
    PatientContext,
    Urgency,
)
from lablens.clinical.safety_disclaimers import SAFETY_LABEL
from lablens.clinical.urgency_rules import evaluate

_BORDERLINE_RANGES: dict[LabType, tuple[float, float]] = {
    # Lab values that, in absence of trend + medication signals, are too ambiguous
    # to classify confidently. Fail safe to INSUFFICIENT_DATA in those windows.
    "POTASSIUM": (5.0, 5.5),
    "CREATININE": (1.2, 1.6),
    "HBA1C": (5.7, 6.5),
}

_REVIEW_PATHS: dict[Urgency, str] = {
    "URGENT": "Clinician review within 4 hours",
    "SOON": "Clinician review within 1-2 business days",
    "ROUTINE": "Clinician review at next scheduled visit",
    "INSUFFICIENT_DATA": "Clinician review recommended; insufficient data for autonomous risk stratification",
}


def _is_borderline(lab_type: LabType, current_value: float) -> bool:
    low, high = _BORDERLINE_RANGES[lab_type]
    return low <= current_value <= high


def classify(
    lab_type: LabType,
    current_value: float,
    unit: str,
    patient_context: PatientContext,
    lab_trend: LabTrendResult,
    medication_interactions: MedicationInteractions,
) -> ClassifierOutput:
    """Risk-stratify an incoming lab result deterministically.

    Returns a structured packet with the rule trace, risk factors, recommended
    review path, and the mandatory safety label (per CLAUDE.md §17).
    """
    expected_unit = LAB_UNIT[lab_type]
    trace: list[str] = []
    risk_factors: list[str] = []

    # Unit sanity (don't fail; just note the discrepancy in the trace)
    if unit and unit.lower() != expected_unit.lower():
        trace.append(
            f"Note: input unit '{unit}' differs from expected '{expected_unit}' for {lab_type}"
        )

    has_trend_data = lab_trend.trend != "INSUFFICIENT_DATA"
    has_meds = medication_interactions.has_significant_interactions
    borderline = _is_borderline(lab_type, current_value)

    # INSUFFICIENT_DATA fail-safe (§6.4): borderline value, no trend, no med signal
    if borderline and not has_trend_data and not has_meds:
        trace.append(
            f"{lab_type} value {current_value} {unit} is borderline; no prior values, "
            "no medication interactions identified"
        )
        trace.append("Fail-safe: returning INSUFFICIENT_DATA rather than guessing")
        return ClassifierOutput(
            urgency="INSUFFICIENT_DATA",
            rule_trace=trace,
            risk_factors=["Borderline value with no clinical context"],
            recommended_review_path=_REVIEW_PATHS["INSUFFICIENT_DATA"],
            safety_label=SAFETY_LABEL,
        )

    condition_displays = [c.display for c in patient_context.active_conditions]
    rule_result = evaluate(
        lab_type=lab_type,
        current_value=current_value,
        patient_condition_displays=condition_displays,
        lab_trend=lab_trend,
        medication_interactions=medication_interactions,
    )

    trace.extend(rule_result.rule_trace)
    risk_factors.extend(rule_result.risk_factors)

    return ClassifierOutput(
        urgency=rule_result.urgency,
        rule_trace=trace,
        risk_factors=risk_factors,
        recommended_review_path=_REVIEW_PATHS[rule_result.urgency],
        safety_label=SAFETY_LABEL,
    )
