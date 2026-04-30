# LabLens demo script (target: under 3:00)

The demo video must (per rules §4) show the project functioning **inside the Prompt Opinion platform**, not just our code running locally.

---

## Cold open (0:00–0:15) — the hook

> Clinicians get 49 to 56 EHR inbox messages a day. Up to 62% of abnormal lab results have documented missed follow-up. The bottleneck isn't reading the lab — it's prioritizing dozens of them while assembling the patient-specific context that determines whether a given result is an emergency or a routine finding. LabLens does that triage step.

Visual: split screen — pile of inbox messages on the left, a clean LabLens triage card on the right.

---

## Setup beat (0:15–0:30) — what they're about to see

> LabLens is a medication-aware lab triage agent submitted to the Prompt Opinion Marketplace. It's a hybrid MCP + A2A submission. The MCP server exposes four healthcare tools; a no-code A2A agent inside Prompt Opinion's workspace orchestrates them. We'll demo the URGENT case: a 68-year-old woman with chronic kidney disease, hypertension, and heart failure, whose new potassium is 6.1.

Visual: Prompt Opinion homepage → workspace → patient list → click `Patient_001_Urgent_Potassium`.

---

## Demo beat (0:30–2:00) — the wow moment

1. **Open the Launchpad.** Patient context: `Patient_001_Urgent_Potassium`. Agent: `LabLens Triage Agent`.

2. **Type the prompt:**
   > Triage today's potassium of 6.1 mmol/L for this patient.

3. **Watch the four tool calls fire** (toggle the tool-calls panel on). Narration:
   > Step 1: get_patient_context. Three active conditions — CKD stage 3b, hypertension, heart failure with reduced ejection fraction. Four active medications.
   >
   > Step 2: get_lab_trend on potassium. Three prior values: 4.6, 4.8, 5.4. Now 6.1. Trend: RISING.
   >
   > Step 3: analyze_medication_lab_interactions. The deterministic step identifies three potassium-raising drug classes — ACE inhibitor, potassium-sparing diuretic, and NSAID. Then a single Claude call narrates each mechanism in plain language, plus a cumulative risk note.
   >
   > Step 4: classify_lab_followup_urgency. Deterministic, with a transparent rule trace. The output is URGENT. Recommended review within 4 hours.

4. **Pause on the rule trace and the cumulative risk note.** This is the wow:
   > The agent identified three independent potassium-raising mechanisms — ACE inhibition, aldosterone receptor blockade, and NSAID-mediated renal hypoperfusion — coexisting in this patient's regimen. None of them alone would push potassium to 6.1, but the combination explains the magnitude. That synthesis is exactly what an LLM does well and what a rule-engine alert system cannot.

---

## Differentiation beat (2:00–2:30) — what this is NOT

> LabLens does not message patients. It does not autonomously place orders. Every output carries a clinician-review-only safety disclaimer. The deterministic classifier produces a rule trace so clinicians can audit any decision. The LLM is constrained to mechanism narration — it cannot invent medications or drug classes. And when inputs are incomplete, it fails safe to INSUFFICIENT_DATA rather than guessing.

Visual: highlight the safety_label, rule_trace, and INSUFFICIENT_DATA test result.

---

## Close (2:30–3:00) — what's next

> LabLens is open source under MIT. Built on Prompt Opinion's MCP framework with the SHARP-on-MCP standard for FHIR context. Repository at github.com/sebtsang/lablens. Discoverable in the Prompt Opinion Marketplace today. Thanks for watching.

Visual: GitHub repo + Marketplace listing card.

---

## Recording checklist

See `demo/recording_checklist.md`.
