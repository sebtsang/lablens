"""Deterministic urgency rules for POTASSIUM, CREATININE, HBA1C.

Implements CLAUDE.md §9 verbatim. Every rule that fires appends a human-readable
trace string. These rules are demo scaffolding (per §9 footnote) — clinicians
would refine thresholds in production. Documented here so the rule trace is
self-explanatory in the demo.

Pure functions, no I/O, no LLM. Same inputs → same outputs.
"""

from dataclasses import dataclass, field

from lablens.clinical.lab_loinc_codes import LabType
from lablens.clinical.models import LabTrendResult, MedicationInteractions, Urgency


@dataclass
class RuleResult:
    urgency: Urgency
    rule_trace: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)


def _has_diabetes_diagnosis(condition_displays: list[str]) -> bool:
    needles = ("diabetes mellitus", "type 2 diabetes", "type 1 diabetes", "t2dm", "t1dm")
    return any(any(n in c.lower() for n in needles) for c in condition_displays)


def evaluate_potassium(
    current_value: float,
    lab_trend: LabTrendResult,
    medication_interactions: MedicationInteractions,
) -> RuleResult:
    """Potassium urgency rules per CLAUDE.md §9."""
    has_meds = medication_interactions.has_significant_interactions
    is_rising = lab_trend.trend == "RISING"
    trace: list[str] = []
    risk_factors: list[str] = []

    # Rule 1: hyperkalemia >= 6.0 → URGENT (always)
    if current_value >= 6.0:
        trace.append(f"K+ = {current_value} mmol/L >= 6.0 → URGENT (severe hyperkalemia threshold)")
        if has_meds:
            risk_factors.append("Active K+-raising medications compound the risk")
        return RuleResult(urgency="URGENT", rule_trace=trace, risk_factors=risk_factors)

    # Rule 2: 5.5+ AND (rising OR med interactions) → URGENT
    if current_value >= 5.5 and (is_rising or has_meds):
        why = "RISING trend" if is_rising else "K+-raising medications"
        trace.append(f"K+ = {current_value} mmol/L >= 5.5 AND {why} → SOON elevated to URGENT")
        if has_meds:
            risk_factors.append("Medication-driven hyperkalemia risk")
        if is_rising:
            risk_factors.append(f"Rising trend (delta {lab_trend.delta_from_baseline})")
        return RuleResult(urgency="URGENT", rule_trace=trace, risk_factors=risk_factors)

    # Rule 3: 5.5+ → SOON
    if current_value >= 5.5:
        trace.append(f"K+ = {current_value} mmol/L >= 5.5 → SOON (moderate hyperkalemia)")
        return RuleResult(urgency="SOON", rule_trace=trace, risk_factors=risk_factors)

    # Rule 4: 5.0+ AND med interactions → SOON
    if current_value >= 5.0 and has_meds:
        trace.append(
            f"K+ = {current_value} mmol/L >= 5.0 AND K+-raising medications → "
            "ROUTINE elevated to SOON"
        )
        risk_factors.append("Medication interactions raise risk at borderline value")
        return RuleResult(urgency="SOON", rule_trace=trace, risk_factors=risk_factors)

    # Rule 5: 5.0+ → ROUTINE
    if current_value >= 5.0:
        trace.append(
            f"K+ = {current_value} mmol/L >= 5.0 → ROUTINE (mild elevation, no risk factors)"
        )
        return RuleResult(urgency="ROUTINE", rule_trace=trace, risk_factors=risk_factors)

    # Rule 6: hypokalemia < 3.5 → SOON (demo simplification)
    if current_value < 3.5:
        trace.append(f"K+ = {current_value} mmol/L < 3.5 → SOON (hypokalemia)")
        return RuleResult(urgency="SOON", rule_trace=trace, risk_factors=risk_factors)

    trace.append(f"K+ = {current_value} mmol/L within normal range → ROUTINE")
    return RuleResult(urgency="ROUTINE", rule_trace=trace, risk_factors=risk_factors)


def evaluate_creatinine(
    current_value: float,
    lab_trend: LabTrendResult,
    medication_interactions: MedicationInteractions,
) -> RuleResult:
    """Creatinine urgency rules per CLAUDE.md §9."""
    has_meds = medication_interactions.has_significant_interactions
    is_rising = lab_trend.trend == "RISING"
    delta = lab_trend.delta_from_baseline or 0.0
    trace: list[str] = []
    risk_factors: list[str] = []

    # Rule 1: > 2.0 AND rising → URGENT
    if current_value > 2.0 and is_rising:
        trace.append(
            f"Creatinine = {current_value} mg/dL > 2.0 AND RISING trend → URGENT (acute kidney injury)"
        )
        risk_factors.append(f"Rising creatinine (delta {delta:+.2f} mg/dL)")
        if has_meds:
            risk_factors.append("Nephrotoxic medications compound the risk")
        return RuleResult(urgency="URGENT", rule_trace=trace, risk_factors=risk_factors)

    # Rule 2: > 1.5 AND large delta from baseline → URGENT
    if current_value > 1.5 and delta >= 0.5:
        trace.append(
            f"Creatinine = {current_value} mg/dL > 1.5 AND delta from baseline "
            f"= {delta:+.2f} mg/dL >= 0.5 → URGENT (significant acute change)"
        )
        risk_factors.append(f"Large delta from baseline ({delta:+.2f} mg/dL)")
        if has_meds:
            risk_factors.append("Nephrotoxic medications compound the risk")
        return RuleResult(urgency="URGENT", rule_trace=trace, risk_factors=risk_factors)

    # Rule 3: > 1.5 AND med interactions → SOON
    if current_value > 1.5 and has_meds:
        trace.append(
            f"Creatinine = {current_value} mg/dL > 1.5 AND nephrotoxic medications "
            "→ SOON elevated from ROUTINE"
        )
        risk_factors.append("Medication-driven nephrotoxicity risk")
        return RuleResult(urgency="SOON", rule_trace=trace, risk_factors=risk_factors)

    # Rule 4: > 1.5 → SOON
    if current_value > 1.5:
        trace.append(
            f"Creatinine = {current_value} mg/dL > 1.5 → SOON (renal impairment threshold)"
        )
        return RuleResult(urgency="SOON", rule_trace=trace, risk_factors=risk_factors)

    # Rule 5: rising AND moderate delta → SOON
    if is_rising and delta >= 0.3:
        trace.append(
            f"Creatinine RISING with delta {delta:+.2f} mg/dL >= 0.3 → SOON "
            "(meaningful upward change even at low absolute value)"
        )
        risk_factors.append("Rising creatinine trend")
        return RuleResult(urgency="SOON", rule_trace=trace, risk_factors=risk_factors)

    trace.append(f"Creatinine = {current_value} mg/dL within tolerance → ROUTINE")
    return RuleResult(urgency="ROUTINE", rule_trace=trace, risk_factors=risk_factors)


def evaluate_hba1c(
    current_value: float,
    patient_condition_displays: list[str],
) -> RuleResult:
    """HbA1c urgency rules per CLAUDE.md §9.

    Note: HbA1c never escalates to URGENT in this demo (per §9 footnote — it's a
    chronic disease marker, not an acute finding).
    """
    has_diabetes = _has_diabetes_diagnosis(patient_condition_displays)
    trace: list[str] = []
    risk_factors: list[str] = []

    # Rule 1: >= 10.0 → SOON (severely uncontrolled)
    if current_value >= 10.0:
        trace.append(f"HbA1c = {current_value}% >= 10.0 → SOON (severely uncontrolled diabetes)")
        return RuleResult(urgency="SOON", rule_trace=trace, risk_factors=risk_factors)

    # Rule 2: >= 9.0 → SOON
    if current_value >= 9.0:
        trace.append(f"HbA1c = {current_value}% >= 9.0 → SOON (poorly controlled)")
        return RuleResult(urgency="SOON", rule_trace=trace, risk_factors=risk_factors)

    # Rule 3: >= 7.0 AND has diabetes → ROUTINE (above target, scheduled follow-up)
    if current_value >= 7.0 and has_diabetes:
        trace.append(
            f"HbA1c = {current_value}% >= 7.0 with established diabetes → ROUTINE "
            "(above target, scheduled diabetes follow-up)"
        )
        return RuleResult(urgency="ROUTINE", rule_trace=trace, risk_factors=risk_factors)

    # Rule 4: >= 6.5 AND no diabetes → SOON (new-diagnosis territory)
    if current_value >= 6.5 and not has_diabetes:
        trace.append(
            f"HbA1c = {current_value}% >= 6.5 with NO diabetes diagnosis → SOON "
            "(new-diagnosis territory)"
        )
        risk_factors.append("Possible new diabetes diagnosis")
        return RuleResult(urgency="SOON", rule_trace=trace, risk_factors=risk_factors)

    trace.append(f"HbA1c = {current_value}% within tolerance → ROUTINE")
    return RuleResult(urgency="ROUTINE", rule_trace=trace, risk_factors=risk_factors)


def evaluate(
    lab_type: LabType,
    current_value: float,
    patient_condition_displays: list[str],
    lab_trend: LabTrendResult,
    medication_interactions: MedicationInteractions,
) -> RuleResult:
    """Top-level dispatch to the per-lab rule function."""
    if lab_type == "POTASSIUM":
        return evaluate_potassium(current_value, lab_trend, medication_interactions)
    if lab_type == "CREATININE":
        return evaluate_creatinine(current_value, lab_trend, medication_interactions)
    if lab_type == "HBA1C":
        return evaluate_hba1c(current_value, patient_condition_displays)
    # Should be unreachable thanks to LabType Literal, but defensive default
    return RuleResult(
        urgency="INSUFFICIENT_DATA",
        rule_trace=[f"Unknown lab type: {lab_type}"],
    )
