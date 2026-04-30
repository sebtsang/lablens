"""Local end-to-end demo runner: walk all 3 authored synthetic patients through the
full LabLens pipeline using mocked FHIR (the JSON bundles) and a real or stub LLM.

Usage:
    uv run python scripts/demo.py                            # stubbed LLM (no key needed)
    GEMINI_API_KEY=... uv run python scripts/demo.py --live-llm                              # uses Gemini (default)
    LABLENS_LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... uv run python scripts/demo.py --live-llm
    LABLENS_LLM_PROVIDER=ollama uv run python scripts/demo.py --live-llm                     # uses local Ollama

This is a debugging / video-backup script. Production demo runs through Prompt
Opinion's UI per prompt_opinion/agent_config.md.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, cast

from anthropic import Anthropic

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

# ruff: noqa: E402
from dataclasses import dataclass

from lablens.clinical.lab_loinc_codes import LabType
from lablens.fhir.client import FhirClient
from lablens.fhir.queries import fetch_lab_trend, fetch_patient_context
from lablens.tools.analyze_medication_lab_interactions import run as analyze
from lablens.tools.classify_lab_followup_urgency import classify

# --- inline stubs (kept here so the script has zero test-suite deps) -----


@dataclass
class _TextBlock:
    text: str
    type: str = "text"


@dataclass
class _Message:
    content: list[_TextBlock]


class _StubMessages:
    def __init__(self, response_text: str) -> None:
        self._response = response_text

    def create(self, **_kwargs: Any) -> _Message:
        return _Message(content=[_TextBlock(text=self._response)])


class _StubAnthropic:
    def __init__(self, response_text: str) -> None:
        self.messages = _StubMessages(response_text)


class _StubFhirClient:
    def __init__(
        self,
        reads: dict[str, dict[str, Any] | None],
        searches: dict[tuple[str, frozenset[tuple[str, str]]], dict[str, Any] | None],
    ) -> None:
        self._reads = reads
        self._searches = searches

    async def read(self, path: str) -> dict[str, Any] | None:
        return self._reads.get(path)

    async def search(
        self,
        resource_type: str,
        search_parameters: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        for (rt, _), bundle in self._searches.items():
            if rt == resource_type:
                return bundle
        return None


DATA_DIR = REPO_ROOT / "data" / "synthetic_patients"

CASES: list[tuple[str, str, LabType, float, str]] = [
    (
        "Patient 1 (URGENT — K+ wow case)",
        "patient_001_urgent_potassium.json",
        "POTASSIUM",
        6.1,
        "mmol/L",
    ),
    (
        "Patient 2 (URGENT — creatinine trend)",
        "patient_002_creatinine_trend.json",
        "CREATININE",
        2.1,
        "mg/dL",
    ),
    ("Patient 3 (SOON — A1c chronic)", "patient_003_a1c_chronic.json", "HBA1C", 9.8, "%"),
]


def _bundle_to_fake_fhir(bundle_path: Path, patient_id: str) -> _StubFhirClient:
    raw = json.loads(bundle_path.read_text())
    entries: list[dict[str, Any]] = raw.get("entry", [])
    by_type: dict[str, list[dict[str, Any]]] = {}
    patient_resource: dict[str, Any] | None = None
    for entry in entries:
        resource = entry.get("resource", {})
        rt = resource.get("resourceType")
        if rt == "Patient":
            patient_resource = resource
        else:
            by_type.setdefault(rt, []).append(resource)

    def bundle_of(resources: list[dict[str, Any]]) -> dict[str, Any] | None:
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [{"resource": r} for r in resources],
        }

    reads: dict[str, dict[str, Any] | None] = {f"Patient/{patient_id}": patient_resource}
    searches: dict[tuple[str, frozenset[tuple[str, str]]], dict[str, Any] | None] = {
        ("Condition", frozenset()): bundle_of(by_type.get("Condition", [])),
        ("MedicationRequest", frozenset()): bundle_of(by_type.get("MedicationRequest", [])),
        ("AllergyIntolerance", frozenset()): bundle_of(by_type.get("AllergyIntolerance", [])),
        ("Encounter", frozenset()): bundle_of(by_type.get("Encounter", [])),
        ("Observation", frozenset()): bundle_of(by_type.get("Observation", [])),
    }
    return _StubFhirClient(reads=reads, searches=searches)


_STUB_LLM_BY_LAB = {
    "POTASSIUM": json.dumps(
        {
            "mechanisms": [
                {
                    "medication": "Lisinopril 20 mg oral tablet",
                    "summary": "ACE inhibition reduces aldosterone, decreasing potassium excretion.",
                },
                {
                    "medication": "Spironolactone 25 mg oral tablet",
                    "summary": "Aldosterone receptor blockade in the distal tubule retains potassium.",
                },
                {
                    "medication": "Ibuprofen 400 mg oral tablet",
                    "summary": "NSAID prostaglandin inhibition reduces renal blood flow and potassium excretion.",
                },
            ],
            "cumulative_risk_note": "Three independent K+-raising mechanisms coexist, compounding hyperkalemia risk.",
        }
    ),
    "CREATININE": json.dumps(
        {
            "mechanisms": [
                {
                    "medication": "Losartan 100 mg oral tablet",
                    "summary": "ARB blockade reduces glomerular filtration pressure.",
                },
                {
                    "medication": "Naproxen 500 mg oral tablet",
                    "summary": "NSAID prostaglandin inhibition reduces afferent arteriolar dilation.",
                },
            ],
            "cumulative_risk_note": "ARB + NSAID synergy compromises glomerular filtration acutely.",
        }
    ),
    "HBA1C": json.dumps(
        {
            "mechanisms": [
                {
                    "medication": "Metformin 1000 mg oral tablet",
                    "summary": "Reduces hepatic gluconeogenesis; lowers A1c.",
                }
            ],
            "cumulative_risk_note": "A1c-lowering medication present; no A1c-raising drugs identified.",
        }
    ),
}


async def _run_case(
    title: str,
    bundle_file: str,
    lab_type: LabType,
    current_value: float,
    unit: str,
    *,
    live_llm: bool,
) -> None:
    print(f"\n{'=' * 80}\n{title}\n{'=' * 80}")
    bundle_path = DATA_DIR / bundle_file
    raw = json.loads(bundle_path.read_text())
    patient_id = next(
        (
            e["resource"]["id"]
            for e in raw["entry"]
            if e["resource"].get("resourceType") == "Patient"
        ),
        "",
    )
    fake = _bundle_to_fake_fhir(bundle_path, patient_id)
    fhir = cast("FhirClient", fake)

    print(f"  • Loading patient context for {patient_id}...")
    patient_context = await fetch_patient_context(fhir, patient_id)
    print(
        f"    age={patient_context.demographics.age}, "
        f"conditions={len(patient_context.active_conditions)}, "
        f"meds={len(patient_context.active_medications)}"
    )

    print(f"  • Computing {lab_type} trend...")
    lab_trend = await fetch_lab_trend(fhir, patient_id, lab_type)
    print(
        f"    values={[v.value for v in lab_trend.values]}, "
        f"trend={lab_trend.trend}, delta={lab_trend.delta_from_baseline}"
    )

    print("  • Analyzing medication-lab interactions...")
    if live_llm:
        # Real LLM call — provider chosen by LABLENS_LLM_PROVIDER env (default gemini)
        interactions = analyze(lab_type, patient_context.active_medications)
    else:
        # Stub: route through the Anthropic test-injection path with a canned response
        anth = cast("Anthropic", _StubAnthropic(_STUB_LLM_BY_LAB[lab_type]))
        interactions = analyze(lab_type, patient_context.active_medications, anthropic_client=anth)
    for it in interactions.interactions_found:
        print(f"    - {it.medication_display} ({it.drug_class}, {it.direction})")
        print(f"      → {it.mechanism_summary}")
    print(f"    cumulative: {interactions.cumulative_risk_note}")

    print(f"  • Classifying urgency for {lab_type}={current_value} {unit}...")
    result = classify(
        lab_type=lab_type,
        current_value=current_value,
        unit=unit,
        patient_context=patient_context,
        lab_trend=lab_trend,
        medication_interactions=interactions,
    )
    print(f"\n    URGENCY: {result.urgency}")
    print(f"    REVIEW PATH: {result.recommended_review_path}")
    print("    RULE TRACE:")
    for t in result.rule_trace:
        print(f"      • {t}")
    if result.risk_factors:
        print("    RISK FACTORS:")
        for r in result.risk_factors:
            print(f"      • {r}")
    print(f"    SAFETY: {result.safety_label}")


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live-llm",
        action="store_true",
        help="Use a real LLM (provider chosen by LABLENS_LLM_PROVIDER, default Gemini).",
    )
    args = parser.parse_args()

    if args.live_llm:
        provider = os.environ.get("LABLENS_LLM_PROVIDER", "gemini").lower()
        required_keys = {
            "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
            "anthropic": ("ANTHROPIC_API_KEY",),
            "ollama": (),
        }
        keys = required_keys.get(provider, ())
        if keys and not any(os.environ.get(k) for k in keys):
            sys.exit(f"{' or '.join(keys)} must be set for --live-llm with provider={provider}")
        print(f"[live-llm] using provider={provider}")

    for title, bundle_file, lab_type, current_value, unit in CASES:
        await _run_case(title, bundle_file, lab_type, current_value, unit, live_llm=args.live_llm)


if __name__ == "__main__":
    asyncio.run(main())
