"""Tests for analyze_medication_lab_interactions — the AI Factor centerpiece."""

from __future__ import annotations

from typing import cast

from anthropic import Anthropic

from lablens.clinical.models import MedicationRef
from lablens.tools.analyze_medication_lab_interactions import run
from tests.fixtures.fake_anthropic import FakeAnthropic

VALID_LLM_RESPONSE = """\
{
  "mechanisms": [
    {"medication": "Lisinopril 20 mg daily", "summary": "Reduces aldosterone, which decreases renal potassium excretion."},
    {"medication": "Spironolactone 25 mg daily", "summary": "Blocks the aldosterone receptor in the distal tubule."},
    {"medication": "Ibuprofen 400 mg TID", "summary": "Inhibits prostaglandin synthesis, reducing renal blood flow and potassium excretion."}
  ],
  "cumulative_risk_note": "Three independent K+-raising drugs coexist in this patient's regimen, compounding risk."
}\
"""


def _three_kplus_meds() -> list[MedicationRef]:
    return [
        MedicationRef(code="1", display="Lisinopril 20 mg daily", drug_class="ACE_INHIBITOR"),
        MedicationRef(
            code="2", display="Spironolactone 25 mg daily", drug_class="POTASSIUM_SPARING_DIURETIC"
        ),
        MedicationRef(code="3", display="Ibuprofen 400 mg TID", drug_class="NSAID"),
    ]


def test_three_drug_potassium_combo_returns_three_interactions_and_significant_flag() -> None:
    fake = cast("Anthropic", FakeAnthropic(VALID_LLM_RESPONSE))
    result = run("POTASSIUM", _three_kplus_meds(), anthropic_client=fake)
    assert len(result.interactions_found) == 3
    assert result.has_significant_interactions is True
    classes = {i.drug_class for i in result.interactions_found}
    assert classes == {"ACE_INHIBITOR", "POTASSIUM_SPARING_DIURETIC", "NSAID"}
    assert all(i.direction == "INCREASES" for i in result.interactions_found)
    assert "Three independent" in result.cumulative_risk_note


def test_no_interacting_meds_returns_empty_with_no_significant_flag() -> None:
    fake = cast("Anthropic", FakeAnthropic(VALID_LLM_RESPONSE))
    meds = [
        MedicationRef(code="1", display="Acetaminophen 500 mg q6h"),  # not in lookup
        MedicationRef(code="2", display="Multivitamin daily"),
    ]
    result = run("POTASSIUM", meds, anthropic_client=fake)
    assert result.interactions_found == []
    assert result.has_significant_interactions is False
    assert "No identified" in result.cumulative_risk_note


def test_decreases_only_meds_are_not_significant() -> None:
    """Metformin DECREASES HbA1c — informational, not a risk signal."""
    fake = cast(
        "Anthropic",
        FakeAnthropic(
            '{"mechanisms":[{"medication":"Metformin 1000 mg BID","summary":"Reduces hepatic glucose."}],'
            ' "cumulative_risk_note":"A1c-lowering drug present."}'
        ),
    )
    meds = [MedicationRef(code="1", display="Metformin 1000 mg BID", drug_class="BIGUANIDE")]
    result = run("HBA1C", meds, anthropic_client=fake)
    assert len(result.interactions_found) == 1
    assert result.interactions_found[0].direction == "DECREASES"
    assert result.has_significant_interactions is False


def test_invalid_llm_json_falls_back_after_retries() -> None:
    fake = cast(
        "Anthropic",
        FakeAnthropic(["not valid json", "still not json", "{nope"]),
    )
    result = run("POTASSIUM", _three_kplus_meds(), anthropic_client=fake)
    # Fallback returns interactions_found populated from deterministic step
    assert len(result.interactions_found) == 3
    # Mechanism summaries are the fallback string
    assert all(
        "Mechanism not well established" in i.mechanism_summary for i in result.interactions_found
    )


def test_drug_class_inference_from_display_when_explicit_class_missing() -> None:
    """If MedicationRef arrives without drug_class, lookup_drug_class fills it in."""
    fake = cast("Anthropic", FakeAnthropic(VALID_LLM_RESPONSE))
    meds = [
        MedicationRef(code="1", display="Lisinopril 20 mg daily"),  # no explicit class
        MedicationRef(code="2", display="Spironolactone 25 mg daily"),
        MedicationRef(code="3", display="Ibuprofen 400 mg TID"),
    ]
    result = run("POTASSIUM", meds, anthropic_client=fake)
    assert len(result.interactions_found) == 3


def test_lab_type_filtering_excludes_irrelevant_drugs() -> None:
    """A patient on lisinopril (K+/Cr) and prednisone (HbA1c) should only get HbA1c-relevant interactions for HBA1C."""
    fake = cast(
        "Anthropic",
        FakeAnthropic(
            '{"mechanisms":[{"medication":"Prednisone 10 mg","summary":"Increases hepatic gluconeogenesis."}],'
            ' "cumulative_risk_note":"Glucocorticoid-driven hyperglycemia."}'
        ),
    )
    meds = [
        MedicationRef(code="1", display="Lisinopril 20 mg daily", drug_class="ACE_INHIBITOR"),
        MedicationRef(code="2", display="Prednisone 10 mg", drug_class="CORTICOSTEROID"),
    ]
    result = run("HBA1C", meds, anthropic_client=fake)
    assert len(result.interactions_found) == 1
    assert result.interactions_found[0].drug_class == "CORTICOSTEROID"
