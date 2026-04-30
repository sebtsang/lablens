# LabLens — Prompt Opinion configuration guide

This is the step-by-step for configuring LabLens inside the Prompt Opinion platform — the no-code A2A agent that judges (and clinicians, in production) actually interact with. Our submission is **hybrid (Path A MCP + no-code A2A)**, which Pawan Jindal (Prompt Opinion) confirmed is encouraged.

> Reference video showing this flow: https://www.youtube.com/watch?v=Qvs_QK4meHc

---

## 0. Prereqs

- A deployed LabLens MCP server reachable at a stable HTTPS URL ending in `/mcp` (Railway is our deploy target — see `railway.json`).
- A Prompt Opinion account at [app.promptopinion.ai](https://app.promptopinion.ai).
- An LLM provider configured (Google AI Studio is fine for the orchestrator side; Anthropic for our MCP server's medication-interaction call is configured separately via `ANTHROPIC_API_KEY` in Railway).

---

## 1. Workspace + synthetic patients

1. Sign in to Prompt Opinion. Create or open a workspace (this *is* the FHIR server in Prompt Opinion's model — every workspace acts as a FHIR R4 backend).
2. Go to **Patients** in the workspace.
3. Add **Patient 1** by uploading the bundle:
   - Click **Upload FHIR Bundle**.
   - Select `data/synthetic_patients/patient_001_urgent_potassium.json` from this repo.
   - Confirm the import. The patient should appear with name `Demo, Patient_001_Urgent_Potassium`, age 68, female.
4. (Optional) Browse the built-in synthetic patients. If any cover trend or chronic-disease cases that match our Patients 2–4 (creatinine trend, HbA1c chronic, insufficient-data), use those rather than authoring more bundles.

---

## 2. Register the LabLens MCP server

1. In the workspace, navigate to **Workspace Hub** → **MCP Servers** → **Add MCP server**.
2. Fields:
   - **Name**: `LabLens`
   - **URL**: `https://<your-railway-domain>/mcp` (e.g., `https://lablens-production.up.railway.app/mcp`)
   - **Transport**: `Streamable HTTP` (the default)
   - **Authentication**: `None` (matches our server config — no auth by default)
   - **FHIR context**: ✅ check this box. This tells Prompt Opinion to pass `X-FHIR-Server-URL`, `X-FHIR-Access-Token`, and `X-Patient-ID` headers on every tool invocation. **Required for our tools to query the workspace's FHIR data.**
3. Click **Test**. You should see four tools listed:
   - `get_patient_context`
   - `get_lab_trend`
   - `analyze_medication_lab_interactions`
   - `classify_lab_followup_urgency`
4. Click **Save**.

---

## 3. Build the no-code "LabLens Triage Agent"

1. Go to **Agents** → **Build your own agents** → **Configure new agent**.
2. Settings:
   - **Name**: `LabLens Triage Agent`
   - **Description**: `Medication-aware lab triage. Given an abnormal lab result and the patient's active medication list, returns a risk-stratified, mechanism-explained action packet for clinician review.`
   - **Scope**: `Patient` (we test in patient context).
   - **System prompt** (override the default):
     ```
     You are a clinician-facing lab triage assistant. When a user asks about a
     patient's lab result, follow this exact workflow:

     1. Call get_patient_context to retrieve the patient's active conditions,
        medications, allergies, and recent encounters.
     2. Call get_lab_trend with the relevant lab type (POTASSIUM, CREATININE, or
        HBA1C) to retrieve recent values and trend.
     3. Call analyze_medication_lab_interactions with the same lab type and the
        patient's active_medications from step 1. This returns mechanism-explained
        drug interactions for that lab.
     4. Call classify_lab_followup_urgency with the lab type, current value, unit,
        and the outputs of steps 1-3. This is the risk stratifier.
     5. Present the result to the clinician: urgency level, recommended review
        path, the rule trace (why this urgency was assigned), the medication
        mechanisms (why these drugs matter), and the safety disclaimer.

     Do not invent clinical thresholds, drug interactions, or recommendations.
     Use only what the tools return. The classifier output is the source of truth
     for urgency.
     ```
3. **Tools**: click **Add**, select all four LabLens tools from the dropdown.
4. **A2A**: ✅ enable A2A so the agent is exposed for hybrid invocation.
5. **FHIR context**: ✅ enable so the agent receives and forwards SHARP context to the MCP tools.
6. **Skills**: add one skill:
   - **Name**: `triage_lab_result`
   - **Description**: `Triage an incoming abnormal lab result for a patient, factoring in active medications.`
7. **Save**.

---

## 4. Smoke test before publishing

1. Open the **Launchpad**.
2. Set scope to **Patient** and select `Patient_001_Urgent_Potassium`.
3. Select the `LabLens Triage Agent`.
4. Send a prompt like:
   > *Triage today's potassium of 6.1 mmol/L for this patient.*
5. Expected behavior:
   - Agent calls `get_patient_context` → returns demographics, 3 active conditions (CKD, HTN, HFrEF), 4 active meds (Lisinopril, Spironolactone, Ibuprofen, Furosemide).
   - Agent calls `get_lab_trend` for POTASSIUM → returns 4 values (4.6 → 4.8 → 5.4 → 6.1), trend RISING.
   - Agent calls `analyze_medication_lab_interactions` with POTASSIUM + active_medications → returns three interactions (ACE_INHIBITOR, POTASSIUM_SPARING_DIURETIC, NSAID), all INCREASES, with cumulative_risk_note explaining the 3-drug stack.
   - Agent calls `classify_lab_followup_urgency` → returns `urgency: URGENT`, rule_trace including "K+ >= 6.0" and the medication signal, recommended_review_path = "Clinician review within 4 hours", safety_label present.
6. Verify the **tool calls panel** shows all four invocations with non-empty payloads.

---

## 5. Publish to Marketplace Studio

Per the rules, publishing is required for Stage 1 (Marketplace Verified). Per the video at 7:00ish:

1. Click **Marketplace Studio** at the bottom of the app.
2. Choose **Add MCP server**.
3. Select the LabLens MCP server you registered in step 2.
4. Fill in:
   - **Display name**: `LabLens — Lab Triage Agent`
   - **One-line description**: `Medication-aware lab triage with deterministic risk + LLM-narrated pharmacology mechanisms.`
   - **Long description**: see `prompt_opinion/marketplace_description.md` (to be authored on D9).
5. Click **Publish**.
6. Confirm the listing appears as discoverable in the Marketplace.

---

## 6. Hand-off for judges

Judges should be able to:
1. Open Prompt Opinion → Marketplace → search "LabLens".
2. Add the MCP server to their workspace (one click).
3. Configure a no-code agent with our four tools (or import a prebuilt configuration if Prompt Opinion supports that).
4. Upload our `patient_001_urgent_potassium.json` bundle (or use any patient with the right medication signature).
5. Send the test prompt and observe the URGENT classification with the 3-drug rule trace.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Test button shows "tools: []" | Streamable HTTP transport not selected, or capability advertisement broken | Verify `/mcp` returns the `ai.promptopinion/fhir-context` extension on initialize |
| Tools fail with "FHIR context missing" | "Pass FHIR context" checkbox unchecked on the MCP server config | Re-check the box and save |
| `analyze_medication_lab_interactions` returns fallback "Mechanism not well established" | `ANTHROPIC_API_KEY` not set on Railway, or model name out of date | Set the env var; check the Railway logs for `interaction_llm_validation_failed` |
| Server returns 502/timeout | Railway instance sleeping or crashed | Check Railway logs; redeploy if needed |
