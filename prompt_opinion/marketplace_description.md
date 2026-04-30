# LabLens — Marketplace listing copy

## Display name
LabLens — Lab Triage Agent

## One-liner
Medication-aware lab triage. Combines deterministic threshold logic with LLM-driven pharmacology reasoning over the patient's active medication list.

## Long description (Marketplace listing)

LabLens turns an incoming abnormal lab result into a risk-stratified, medication-aware action packet for clinician review.

The bottleneck in clinical inbox triage isn't reading a lab — it's prioritizing dozens per day while assembling the patient-specific context (active conditions, medications, prior trends) that determines whether a given result is an emergency or a routine finding. Published studies put the EHR inbox load at 49–56 messages per clinician per day, with 6.8–62% of abnormal lab results having documented missed follow-up. The medication-context piece is the wedge: a potassium of 6.1 mmol/L is concerning in any patient, but in a patient on lisinopril + spironolactone + ibuprofen — three drugs that each independently raise potassium — it is significantly more dangerous.

LabLens exposes four MCP tools that work together:
- **get_patient_context** — pulls active conditions, active medications (with drug-class enrichment), allergies, and recent encounters from the workspace's FHIR data.
- **get_lab_trend** — recent values plus a coarse RISING/FALLING/STABLE label for POTASSIUM, CREATININE, or HBA1C.
- **analyze_medication_lab_interactions** — the differentiator. A deterministic drug-class lookup identifies which medications interact with the lab type; a single Anthropic Claude call generates plain-language mechanism summaries and a cumulative risk narrative. The LLM is constrained to mechanism narration only — it cannot add medications or invent drug classes.
- **classify_lab_followup_urgency** — pure deterministic risk stratifier. Same inputs always produce same outputs. Returns urgency, a transparent rule trace, recommended review path, and a safety disclaimer. Fails safe to INSUFFICIENT_DATA when inputs are incomplete rather than guessing.

LabLens is **clinician-facing**. It does not message patients. It does not autonomously place orders. Every output carries the disclaimer "For clinician review only. Synthetic demo. Not autonomous medical advice."

Synthetic data only — never real PHI. Built for the Agents Assemble Healthcare AI Hackathon, deadline May 11, 2026.

## Tags
healthcare, fhir, mcp, lab-triage, clinical-decision-support, pharmacology, hackathon, agents-assemble

## Repository
https://github.com/sebtsang/lablens

## License
MIT
