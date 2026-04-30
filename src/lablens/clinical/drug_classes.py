"""Drug-class lookup table.

Verbatim from CLAUDE.md §7. The team validated these classifications against
standard pharmacology references; do not modify entries without team approval
(per CLAUDE.md §16 item 3).

Match by case-insensitive substring of the medication display name.
"""

from typing import TypedDict


class DrugClassEntry(TypedDict):
    drug_class: str
    affects_labs: list[str]


# Each entry should be lowercase, singular, no brand names.
DRUG_CLASS_LOOKUP: dict[str, DrugClassEntry] = {
    # ACE inhibitors — raise K+, can raise creatinine
    "lisinopril": {"drug_class": "ACE_INHIBITOR", "affects_labs": ["POTASSIUM", "CREATININE"]},
    "enalapril": {"drug_class": "ACE_INHIBITOR", "affects_labs": ["POTASSIUM", "CREATININE"]},
    "ramipril": {"drug_class": "ACE_INHIBITOR", "affects_labs": ["POTASSIUM", "CREATININE"]},
    "perindopril": {"drug_class": "ACE_INHIBITOR", "affects_labs": ["POTASSIUM", "CREATININE"]},
    # ARBs — raise K+, can raise creatinine
    "losartan": {"drug_class": "ARB", "affects_labs": ["POTASSIUM", "CREATININE"]},
    "valsartan": {"drug_class": "ARB", "affects_labs": ["POTASSIUM", "CREATININE"]},
    "irbesartan": {"drug_class": "ARB", "affects_labs": ["POTASSIUM", "CREATININE"]},
    "candesartan": {"drug_class": "ARB", "affects_labs": ["POTASSIUM", "CREATININE"]},
    # Potassium-sparing diuretics — raise K+
    "spironolactone": {"drug_class": "POTASSIUM_SPARING_DIURETIC", "affects_labs": ["POTASSIUM"]},
    "eplerenone": {"drug_class": "POTASSIUM_SPARING_DIURETIC", "affects_labs": ["POTASSIUM"]},
    "amiloride": {"drug_class": "POTASSIUM_SPARING_DIURETIC", "affects_labs": ["POTASSIUM"]},
    "triamterene": {"drug_class": "POTASSIUM_SPARING_DIURETIC", "affects_labs": ["POTASSIUM"]},
    # NSAIDs — raise K+ and creatinine via renal mechanism
    "ibuprofen": {"drug_class": "NSAID", "affects_labs": ["POTASSIUM", "CREATININE"]},
    "naproxen": {"drug_class": "NSAID", "affects_labs": ["POTASSIUM", "CREATININE"]},
    "diclofenac": {"drug_class": "NSAID", "affects_labs": ["POTASSIUM", "CREATININE"]},
    "celecoxib": {"drug_class": "NSAID", "affects_labs": ["POTASSIUM", "CREATININE"]},
    "indomethacin": {"drug_class": "NSAID", "affects_labs": ["POTASSIUM", "CREATININE"]},
    # Other nephrotoxic agents (creatinine-relevant)
    "vancomycin": {"drug_class": "NEPHROTOXIC_ANTIBIOTIC", "affects_labs": ["CREATININE"]},
    "gentamicin": {"drug_class": "AMINOGLYCOSIDE", "affects_labs": ["CREATININE"]},
    "tobramycin": {"drug_class": "AMINOGLYCOSIDE", "affects_labs": ["CREATININE"]},
    "amikacin": {"drug_class": "AMINOGLYCOSIDE", "affects_labs": ["CREATININE"]},
    "tacrolimus": {"drug_class": "CALCINEURIN_INHIBITOR", "affects_labs": ["CREATININE"]},
    "cyclosporine": {"drug_class": "CALCINEURIN_INHIBITOR", "affects_labs": ["CREATININE"]},
    # Glucose-affecting drugs (HbA1c-relevant)
    "prednisone": {"drug_class": "CORTICOSTEROID", "affects_labs": ["HBA1C"]},
    "dexamethasone": {"drug_class": "CORTICOSTEROID", "affects_labs": ["HBA1C"]},
    "methylprednisolone": {"drug_class": "CORTICOSTEROID", "affects_labs": ["HBA1C"]},
    "olanzapine": {"drug_class": "ATYPICAL_ANTIPSYCHOTIC", "affects_labs": ["HBA1C"]},
    "quetiapine": {"drug_class": "ATYPICAL_ANTIPSYCHOTIC", "affects_labs": ["HBA1C"]},
    # Lower A1c — included for context, not flagged as risk
    "metformin": {"drug_class": "BIGUANIDE", "affects_labs": ["HBA1C"]},
    "insulin": {"drug_class": "INSULIN", "affects_labs": ["HBA1C"]},
}


def lookup_drug_class(medication_display: str) -> DrugClassEntry | None:
    """Case-insensitive substring match of a medication display name to a drug class entry."""
    normalized = medication_display.lower()
    for key, entry in DRUG_CLASS_LOOKUP.items():
        if key in normalized:
            return entry
    return None
