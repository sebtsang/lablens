"""Prompt templates for analyze_medication_lab_interactions (CLAUDE.md §8).

System prompt is verbatim from §8 — do not modify without team approval. The
LLM is constrained to mechanism narration only; it does NOT add medications,
invent drug classes, or recommend interventions.
"""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are a clinical pharmacology expert. You will be given:
1. A lab type (POTASSIUM, CREATININE, or HBA1C)
2. A list of medications the patient is taking that have been pre-identified as interacting with this lab type, along with their drug class and the direction of effect (INCREASES, DECREASES, or VARIABLE).

Your task is to:
A. For each medication, write a 1-2 sentence mechanism summary in plain language. State the mechanism (e.g., "reduces aldosterone-mediated potassium excretion"). Do not exceed 2 sentences.
B. Write a 1-2 sentence cumulative risk note describing the overall medication-driven risk picture for this patient. If multiple medications all push the lab in the same direction, say so explicitly.

CONSTRAINTS — these are absolute:
- Do NOT add medications that are not in the input list.
- Do NOT invent drug classes or mechanisms not supported by standard pharmacology.
- Do NOT recommend stopping, changing, or starting medications.
- Do NOT diagnose or treat. You are explaining mechanisms only.
- If you are uncertain about a mechanism, write "Mechanism not well established" rather than guessing.

Output JSON in exactly this shape:
{
  "mechanisms": [
    { "medication": "<name>", "summary": "<1-2 sentences>" }
  ],
  "cumulative_risk_note": "<1-2 sentences>"
}\
"""


def build_user_prompt(lab_type: str, identified_interactions: list[tuple[str, str, str]]) -> str:
    """Format the user prompt for the medication-interaction LLM call.

    `identified_interactions` is a pre-classified list of (medication_display, drug_class, direction)
    tuples produced by the deterministic step. The LLM only generates the mechanism narration.
    """
    lines = [f"Lab type: {lab_type}", "Medications interacting with this lab:"]
    for name, drug_class, direction in identified_interactions:
        lines.append(f"- {name} ({drug_class}, {direction})")
    lines.append("")
    lines.append("Generate the JSON output as specified.")
    return "\n".join(lines)
