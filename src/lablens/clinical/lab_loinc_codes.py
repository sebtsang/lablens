"""LOINC constants and the LabType literal for the three target labs (per CLAUDE.md §9)."""

from typing import Literal

LabType = Literal["POTASSIUM", "CREATININE", "HBA1C"]

POTASSIUM_LOINC = "2823-3"
CREATININE_LOINC = "2160-0"
HBA1C_LOINC = "4548-4"

LOINC_BY_LAB_TYPE: dict[LabType, str] = {
    "POTASSIUM": POTASSIUM_LOINC,
    "CREATININE": CREATININE_LOINC,
    "HBA1C": HBA1C_LOINC,
}

LAB_DISPLAY: dict[LabType, str] = {
    "POTASSIUM": "Potassium [Moles/volume] in Serum or Plasma",
    "CREATININE": "Creatinine [Mass/volume] in Serum or Plasma",
    "HBA1C": "Hemoglobin A1c/Hemoglobin.total in Blood",
}

LAB_UNIT: dict[LabType, str] = {
    "POTASSIUM": "mmol/L",
    "CREATININE": "mg/dL",
    "HBA1C": "%",
}
