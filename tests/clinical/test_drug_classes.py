"""Tests for the drug-class lookup table (CLAUDE.md §7)."""

import pytest

from lablens.clinical.drug_classes import DRUG_CLASS_LOOKUP, lookup_drug_class


@pytest.mark.parametrize(
    ("medication", "expected_class"),
    [
        ("Lisinopril 20 mg daily", "ACE_INHIBITOR"),
        ("LOSARTAN 100 mg", "ARB"),
        ("spironolactone 25mg", "POTASSIUM_SPARING_DIURETIC"),
        ("Ibuprofen 400 mg TID", "NSAID"),
        ("Vancomycin IV", "NEPHROTOXIC_ANTIBIOTIC"),
        ("Gentamicin", "AMINOGLYCOSIDE"),
        ("Tacrolimus 1mg BID", "CALCINEURIN_INHIBITOR"),
        ("Prednisone 10 mg daily", "CORTICOSTEROID"),
        ("Olanzapine 5 mg", "ATYPICAL_ANTIPSYCHOTIC"),
        ("Metformin 1000 mg BID", "BIGUANIDE"),
        ("Insulin glargine", "INSULIN"),
    ],
)
def test_lookup_recognizes_common_medications(medication: str, expected_class: str) -> None:
    entry = lookup_drug_class(medication)
    assert entry is not None
    assert entry["drug_class"] == expected_class


def test_lookup_returns_none_for_unrecognized_drug() -> None:
    assert lookup_drug_class("acetaminophen") is None
    assert lookup_drug_class("aspirin") is None


def test_every_table_entry_has_at_least_one_affected_lab() -> None:
    for med, entry in DRUG_CLASS_LOOKUP.items():
        assert entry["affects_labs"], f"{med} has no affected labs"


def test_table_keys_are_lowercase_no_brand_names() -> None:
    for key in DRUG_CLASS_LOOKUP:
        assert key == key.lower(), f"{key} should be lowercase"
        assert " " not in key, f"{key} should be a single token"
