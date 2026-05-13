# LabLens v3 — Codex Handoff Document

**Project:** LabLens — A medication-aware lab triage agent for the Agents Assemble Healthcare AI Hackathon (Prompt Opinion / Devpost).
**Submission deadline:** Monday, May 11, 2026, 11:00 PM ET.
**Team:** Two fourth-year biomed students.
**Audience for this document:** Codex (or another agentic coding assistant) acting as the implementation partner for this team.

---

## 0. Pre-flight: workspace setup (do this FIRST, before reading the rest)

This document assumes you are running inside a project folder that has been initialized as a Git repository. If you are NOT — i.e., the team just opened Codex in an empty folder and pointed you at this file — your very first job is to set up the workspace correctly. Walk through these steps in order. Do NOT skip ahead to clinical implementation.

### 0.1 Verify you are in the right folder

Run `pwd` and `ls -la`. You should be in a folder named `lablens` (or similar) and you should see this `AGENTS.md` file. If you don't see `AGENTS.md` in the listing, stop and ask the team where to find it.

### 0.2 Initialize Git if not already done

Check whether Git is initialized:
```
git rev-parse --is-inside-work-tree 2>/dev/null
```

If that returns `false` or errors, initialize:
```
git init -b main
git config user.name "<ask the team for their name>"
git config user.email "<ask the team for their email>"
```

Ask the team for their preferred Git identity before running `git config` — do NOT guess.

### 0.3 Create a `.gitignore` immediately

Before any other file. Create `.gitignore` at the repo root with this content (do not modify or trim — this is the minimum safe baseline):

```
# Dependencies
node_modules/
.pnp
.pnp.js

# Build output
dist/
build/
*.tsbuildinfo

# Environment / secrets
.env
.env.local
.env.*.local
*.pem
*.key

# Logs
logs/
*.log
npm-debug.log*

# OS / editor
.DS_Store
Thumbs.db
.vscode/
.idea/
*.swp

# Test artifacts
coverage/
.nyc_output/

# FHIR / clinical artifacts (paranoia — never commit anything that could be PHI)
data/real_patients/
data/exports/
*.phi.json

# Codex session artifacts
.Codex/
```

The `data/real_patients/` and `*.phi.json` lines are intentional belt-and-suspenders. Even though we will never use real PHI, this protects against accidents.

### 0.4 Create a basic `README.md`

Stub-level only — the polished version comes later (section 15). For now:

```markdown
# LabLens

A medication-aware lab triage agent for the Agents Assemble Healthcare AI Hackathon.

**Status:** Under active development.
**Hackathon submission deadline:** May 11, 2026.

See `AGENTS.md` for the full project plan.
```

### 0.5 First commit

Stage and commit these initial files:
```
git add .gitignore README.md AGENTS.md
git commit -m "Initial commit: project setup and handoff doc"
```

### 0.6 Ask the team about the GitHub remote

The team needs a public GitHub repository for hackathon submission (see section 1). Ask them:

> Have you created a GitHub repo yet? If yes, what's the SSH or HTTPS URL? If no, please create one (suggested name: `lablens`, MIT license, public) and share the URL with me.

Once they share a URL, add the remote and push:
```
git remote add origin <URL_FROM_TEAM>
git push -u origin main
```

If the team hasn't created the repo yet, that's fine — keep building locally and add the remote once they do. Do not block on this. Push to main is allowed throughout day 1–3 (rapid scaffolding); switch to feature branches starting day 4.

### 0.7 Verify Node and tooling

Check versions:
```
node --version    # need 20+
npm --version
```

If Node is older than 20, stop and ask the team to upgrade before continuing.

### 0.8 Set up environment variables (skeleton only — no secrets)

Create `.env.example` at the repo root:

```
# Anthropic API for the medication-interaction LLM tool
# Get a key at https://console.anthropic.com
ANTHROPIC_API_KEY=

# FHIR test server (default: public HAPI test server)
DEFAULT_FHIR_SERVER_URL=https://hapi.fhir.org/baseR4

# Server port for local development
PORT=8000

# Set to "development" for local, "production" for deployed
NODE_ENV=development
```

Do NOT create `.env` (the actual secrets file). The team will create that themselves and never commit it. The `.gitignore` already excludes `.env`.

Commit this:
```
git add .env.example
git commit -m "Add environment variable template"
```

### 0.9 Now (and only now) read the rest of this document

You're set up. Continue to "How to use this document" below.

---

## Git workflow rules (apply for the entire project)

- **Never commit secrets.** If you find yourself about to write an API key into any file other than the team's local `.env`, stop. The `.gitignore` should already exclude `.env`, but double-check.
- **Never commit anything that could be real patient data.** All synthetic patients live in `data/synthetic_patients/` and are clearly named (e.g., `patient_001_urgent_potassium.json`). If you ever encounter a file with a real-looking name, MRN, or birthdate, stop and ask the team.
- **Commit message style:** Imperative mood, ~50 char subject line, optional body. Example: `Add classify_lab_followup_urgency tool with K+ rules`.
- **Days 1–3:** Commit directly to `main`. Rapid scaffolding phase.
- **Days 4 onwards:** Feature branches per section of work. Branch naming: `feature/<short-description>` (e.g., `feature/medication-interaction-tool`). Open a PR, self-review, then merge.
- **Push frequently.** At minimum once per work session. The hackathon judges may look at the commit history; a healthy commit cadence signals real work.
- **Tag the submission commit.** When the team is ready to submit on May 11, tag that commit `v1.0.0-submission`.

---

## How to use this document

Read this entire document once before writing any code. It contains everything you need to know about what to build, what NOT to build, what's already decided, and where to ask before guessing. The team has done the strategic and clinical work; your job is to translate it into a working submission.

When in doubt, **prefer asking the team** over guessing. The team has clinical knowledge you don't and doesn't expect you to invent clinical content. They explicitly do NOT want you to:

- Invent clinical thresholds, drug-interaction rules, or scoring logic that isn't grounded in this document
- Add patient-message drafting, multi-specialty coverage, or "promise tracking" features
- Use real or partially-real PHI from any dataset, even examples
- Expand the scope to additional lab types, additional drug classes, or additional clinical conditions

When the document says "do X," do X. When it says "ask before doing Y," ask before doing Y. When it says "do NOT do Z," do NOT do Z under any circumstances.

---

## 1. The hackathon constraints (non-negotiable)

Read these first. Violations of any of these mean the submission fails Stage 1 and is never judged.

| Constraint | Detail |
|---|---|
| Platform | Submission must be published to and discoverable in the **Prompt Opinion Marketplace** at app.promptopinion.ai. If it's not in the marketplace, it doesn't count. |
| Protocol | Must adhere to **MCP** (Model Context Protocol) and/or **A2A** (Agent-to-Agent). LabLens uses both: MCP server with deterministic clinical tools, A2A agent for orchestration. |
| Healthcare context | Must use the **SHARP** (Standardised Healthcare Agent Remote Protocol) extension headers: `X-FHIR-Server-URL`, `X-FHIR-Access-Token`, `X-Patient-ID`. The MCP server must NOT run its own OAuth flow. |
| Data | **Synthetic or de-identified data only.** No real PHI in source code, logs, screenshots, demo video, or Devpost text. Use the public HAPI FHIR test server (hapi.fhir.org/baseR4) for FHIR plumbing; use hand-authored synthetic patients for the clinical demo. |
| Demo video | Under 3 minutes, publicly hosted (YouTube/Vimeo), shows the project working inside Prompt Opinion. |
| Submission medium | Devpost. Project must include a public GitHub repo with MIT license. |

If anything you're about to do would violate one of these, stop and flag it to the team.

---

## 2. The product, in one sentence

**LabLens turns an incoming abnormal lab result into a risk-stratified, medication-aware action packet for clinician review — by combining deterministic threshold logic with LLM-driven pharmacology reasoning over the patient's active medication list.**

That sentence is the project. Everything in the repo serves it. If a feature doesn't directly support this sentence, it doesn't get built.

---

## 3. Why this project exists (clinical motivation)

You don't need to invent clinical content, but you need enough context to make good architecture decisions.

The problem: clinicians receive ~49–56 EHR inbox messages per day in published studies, and 6.8%–62% of abnormal lab results have documented missed follow-up. The bottleneck isn't *understanding* a lab result — it's prioritizing dozens of them while assembling the patient-specific context (active conditions, medications, prior trends) that determines whether a given result is an emergency or a routine finding.

The medication-context piece is the wedge. A potassium of 6.1 mmol/L is concerning in any patient, but in a patient on lisinopril + spironolactone + ibuprofen — three drugs that each independently raise potassium — it is significantly more dangerous. This kind of pharmacology synthesis is exactly what an LLM can do well and exactly what a rule-engine alert system cannot.

LabLens is **clinician-facing**. It does not message patients. It does not autonomously place orders. It produces a risk-stratified packet that a clinician reviews and acts on.

---

## 4. Differentiation from the competing project

There is one other public submission in this hackathon's GitHub topic that touches a similar space: `prabhakaran-jm/clinical-promise-keeper`. The team has already analyzed it. **Do not replicate any of its design.** The repositioning the team chose is:

| Promise Keeper (existing competitor) | LabLens (this project) |
|---|---|
| Looks **backward** at chart notes for unfulfilled promises | Looks **forward** at a new lab result that just arrived |
| Does NOT read MedicationRequest resources | Reads MedicationRequest as a core input |
| Outputs draft FHIR Task resources | Outputs a clinician-facing risk packet with rule trace |
| Generic across 8 clinical specialties | Goes deep on 3 lab types with real pharmacology reasoning |
| Trigger: "what did we say we'd do that's still pending?" | Trigger: "this just arrived — how worried should we be?" |

If a design choice would make LabLens look like Promise Keeper, choose differently. The two projects should be obviously distinct to a judge who reads both READMEs.

---

## 5. Architecture (already decided — implement this; do not redesign)

```
┌──────────────────────────────────────────────────────────────┐
│                    Prompt Opinion Platform                    │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │             LabLens A2A Orchestrator Agent              │ │
│  │  (configured no-code in Prompt Opinion's agent builder) │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                   │
│                            │ MCP / JSON-RPC                    │
│                            ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │          LabLens MCP Server (TypeScript, deployed)       │ │
│  │                                                            │ │
│  │   Tools exposed:                                           │ │
│  │   • get_patient_context                                    │ │
│  │   • get_lab_trend                                          │ │
│  │   • analyze_medication_lab_interactions                    │ │
│  │   • classify_lab_followup_urgency                          │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                   │
│                            │ SHARP headers + FHIR REST         │
│                            ▼                                   │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  HAPI FHIR test svr  │
                  │  hapi.fhir.org/baseR4│
                  │                      │
                  │  Synthetic patients  │
                  │  loaded by us at     │
                  │  setup time          │
                  └──────────────────────┘
```

**Important architectural notes:**

- The MCP server must implement the SHARP headers model. It does NOT run OAuth itself. It reads `X-FHIR-Server-URL`, `X-FHIR-Access-Token`, and `X-Patient-ID` from each request and forwards them when calling FHIR. Reference implementation pattern: `sharp-fhir-mcp` repo by TerminallyLazy on GitHub. Spec: sharponmcp.com.
- The MCP server must advertise `capabilities.experimental.fhir_context_required = true` on every initialize response.
- The A2A agent is configured **inside the Prompt Opinion platform's no-code agent builder**. We do NOT write A2A protocol code from scratch. The platform handles A2A.
- The MCP server is what we build with code. It's the "hammer" in Prompt Opinion's framing.
- Language: **TypeScript** for the MCP server. (Note: Prompt Opinion's reference `po-community-mcp` is in C#, but we are NOT extending that — we are building our own MCP server. We choose TypeScript because the official MCP TypeScript SDK is mature and the team is comfortable with it.)
- Deployment: containerized, deployable to Cloud Run or any container host. Environment variables, not hardcoded secrets.

---

## 6. The four MCP tools — exact contracts

Implement exactly these four tools. Do not add tools without asking. Do not split or merge tools without asking.

### 6.1 `get_patient_context`

**Purpose:** Pull the patient's active conditions, active medications, allergies, and recent encounters from FHIR.

**Input:** None beyond SHARP headers (the patient ID is in `X-Patient-ID`).

**Output:**
```typescript
{
  patient_id: string;
  demographics: { age: number; sex: string };
  active_conditions: Array<{ code: string; display: string; onset_date?: string }>;
  active_medications: Array<{
    code: string;          // RxNorm if available
    display: string;       // human-readable name
    dose?: string;
    frequency?: string;
    drug_class?: string;   // e.g., "ACE_INHIBITOR", "ARB", "POTASSIUM_SPARING_DIURETIC", "NSAID"
  }>;
  allergies: Array<{ substance: string; reaction?: string; severity?: string }>;
  recent_encounters: Array<{ date: string; type: string; reason?: string }>;
}
```

**Implementation notes:**
- Query FHIR resources: `Condition` (clinical-status=active), `MedicationRequest` (status=active), `AllergyIntolerance`, `Encounter` (date>=now-6months).
- For `drug_class`, maintain a small lookup table mapping RxNorm codes (or names if codes unavailable) to drug classes relevant to the three target labs. See section 7 for the drug class lookup.
- Fail gracefully: if a FHIR query returns nothing, return an empty array for that field — do NOT make up data.

### 6.2 `get_lab_trend`

**Purpose:** Get the recent values for a specific lab, so the classifier can reason about trend (rising/falling/stable).

**Input:**
```typescript
{ lab_loinc_code: string; lookback_months?: number /* default 12 */ }
```

**Output:**
```typescript
{
  lab_code: string;
  lab_display: string;     // e.g., "Potassium [Moles/volume] in Serum or Plasma"
  unit: string;
  values: Array<{ value: number; effective_date: string; reference_low?: number; reference_high?: number }>;
  trend: "RISING" | "FALLING" | "STABLE" | "INSUFFICIENT_DATA";
  delta_from_baseline?: number;
}
```

**Implementation notes:**
- Query FHIR `Observation` resources matching the LOINC code, sorted by `effectiveDateTime` descending.
- Trend logic: compare most recent to the median of the prior 3 values. RISING if increase >10%, FALLING if decrease >10%, STABLE otherwise. INSUFFICIENT_DATA if fewer than 2 prior values.
- These thresholds are demo scaffolding. Document them clearly in code comments as "demo heuristic, not clinical guidance."

### 6.3 `analyze_medication_lab_interactions` ⭐ (this is the differentiator)

**Purpose:** Identify medications that interact with this lab type and explain the mechanism. This is the AI Factor centerpiece — it combines a deterministic drug-class lookup with LLM-generated mechanism narration.

**Input:**
```typescript
{
  lab_type: "POTASSIUM" | "CREATININE" | "HBA1C";
  active_medications: Array<{ display: string; drug_class?: string }>;
}
```

**Output:**
```typescript
{
  interactions_found: Array<{
    medication_display: string;
    drug_class: string;
    direction: "INCREASES" | "DECREASES" | "VARIABLE";
    mechanism_summary: string;       // LLM-generated, 1-2 sentences, plain language
    evidence_strength: "WELL_ESTABLISHED" | "MODERATE" | "LIMITED";
  }>;
  cumulative_risk_note: string;     // LLM-generated, e.g., "Three independent K+-raising drugs coexist in this patient's regimen."
  has_significant_interactions: boolean;
}
```

**Implementation notes:**
- **Deterministic step (no LLM):** Walk the active medication list, classify each into a drug class via the lookup table in section 7, and identify which classes interact with the requested lab type. This step produces a structured list of (medication, class, direction) tuples.
- **LLM step (Codex, GPT, or Gemini — pick one and stick with it):** For each identified interaction, generate the `mechanism_summary` field using a tightly constrained prompt (see section 8). For the `cumulative_risk_note`, generate a 1-2 sentence summary of the overall medication-driven risk picture.
- The LLM is NOT allowed to add medications that aren't in the active list, nor to invent drug classes. It is only generating natural-language explanations of structured findings.
- If no interactions are found, return `interactions_found: []`, `cumulative_risk_note: "No identified medication interactions for this lab type."`, `has_significant_interactions: false`.

### 6.4 `classify_lab_followup_urgency`

**Purpose:** The deterministic risk-stratification core. Given the lab result, the patient context, the trend, and the medication interactions, classify urgency and produce a transparent rule trace.

**Input:**
```typescript
{
  lab_type: "POTASSIUM" | "CREATININE" | "HBA1C";
  current_value: number;
  unit: string;
  patient_context: /* output of get_patient_context */;
  lab_trend: /* output of get_lab_trend */;
  medication_interactions: /* output of analyze_medication_lab_interactions */;
}
```

**Output:**
```typescript
{
  urgency: "URGENT" | "SOON" | "ROUTINE" | "INSUFFICIENT_DATA";
  rule_trace: Array<string>;         // Human-readable list of rules that fired, in order
  risk_factors: Array<string>;       // Patient-specific factors that influenced the classification
  recommended_review_path: string;   // e.g., "Clinician review within 4 hours"
  safety_label: string;              // Always: "For clinician review only. Synthetic demo. Not autonomous medical advice."
}
```

**Implementation notes:**
- This function is **pure and deterministic**. Same inputs → same outputs, every time. No LLM calls. Unit-test every branch.
- Rule logic for the three labs is in section 9.
- If `lab_trend.trend === "INSUFFICIENT_DATA"` AND no medication interactions are identified AND the value is in the borderline range, return `urgency: "INSUFFICIENT_DATA"` with a rule trace explaining why. **The agent must fail safely on missing data, not guess.**

---

## 7. Drug class lookup table (build this exactly)

Hard-code this table in a file called `src/clinical/drug_classes.ts`. Document each entry with a 1-line comment citing the mechanism. The team has already validated this table against pharmacology references — do not modify entries without asking.

```typescript
// Drug class assignments for medications relevant to the three target lab types.
// These classifications are based on standard pharmacology references.
// Each entry should be lowercase, singular, no brand names — match by case-insensitive substring.

export const DRUG_CLASS_LOOKUP: Record<string, { class: string; affects_labs: string[] }> = {
  // ACE inhibitors — raise K+, can raise creatinine
  "lisinopril":   { class: "ACE_INHIBITOR", affects_labs: ["POTASSIUM", "CREATININE"] },
  "enalapril":    { class: "ACE_INHIBITOR", affects_labs: ["POTASSIUM", "CREATININE"] },
  "ramipril":     { class: "ACE_INHIBITOR", affects_labs: ["POTASSIUM", "CREATININE"] },
  "perindopril":  { class: "ACE_INHIBITOR", affects_labs: ["POTASSIUM", "CREATININE"] },

  // ARBs — raise K+, can raise creatinine
  "losartan":     { class: "ARB", affects_labs: ["POTASSIUM", "CREATININE"] },
  "valsartan":    { class: "ARB", affects_labs: ["POTASSIUM", "CREATININE"] },
  "irbesartan":   { class: "ARB", affects_labs: ["POTASSIUM", "CREATININE"] },
  "candesartan":  { class: "ARB", affects_labs: ["POTASSIUM", "CREATININE"] },

  // Potassium-sparing diuretics — raise K+
  "spironolactone": { class: "POTASSIUM_SPARING_DIURETIC", affects_labs: ["POTASSIUM"] },
  "eplerenone":     { class: "POTASSIUM_SPARING_DIURETIC", affects_labs: ["POTASSIUM"] },
  "amiloride":      { class: "POTASSIUM_SPARING_DIURETIC", affects_labs: ["POTASSIUM"] },
  "triamterene":    { class: "POTASSIUM_SPARING_DIURETIC", affects_labs: ["POTASSIUM"] },

  // NSAIDs — raise K+ and creatinine via renal mechanism
  "ibuprofen":   { class: "NSAID", affects_labs: ["POTASSIUM", "CREATININE"] },
  "naproxen":    { class: "NSAID", affects_labs: ["POTASSIUM", "CREATININE"] },
  "diclofenac":  { class: "NSAID", affects_labs: ["POTASSIUM", "CREATININE"] },
  "celecoxib":   { class: "NSAID", affects_labs: ["POTASSIUM", "CREATININE"] },
  "indomethacin":{ class: "NSAID", affects_labs: ["POTASSIUM", "CREATININE"] },

  // Other nephrotoxic agents (creatinine-relevant)
  "vancomycin":   { class: "NEPHROTOXIC_ANTIBIOTIC", affects_labs: ["CREATININE"] },
  "gentamicin":   { class: "AMINOGLYCOSIDE", affects_labs: ["CREATININE"] },
  "tobramycin":   { class: "AMINOGLYCOSIDE", affects_labs: ["CREATININE"] },
  "amikacin":     { class: "AMINOGLYCOSIDE", affects_labs: ["CREATININE"] },
  "tacrolimus":   { class: "CALCINEURIN_INHIBITOR", affects_labs: ["CREATININE"] },
  "cyclosporine": { class: "CALCINEURIN_INHIBITOR", affects_labs: ["CREATININE"] },

  // Glucose-affecting drugs (HbA1c-relevant)
  "prednisone":      { class: "CORTICOSTEROID", affects_labs: ["HBA1C"] },
  "dexamethasone":   { class: "CORTICOSTEROID", affects_labs: ["HBA1C"] },
  "methylprednisolone": { class: "CORTICOSTEROID", affects_labs: ["HBA1C"] },
  "olanzapine":      { class: "ATYPICAL_ANTIPSYCHOTIC", affects_labs: ["HBA1C"] },
  "quetiapine":      { class: "ATYPICAL_ANTIPSYCHOTIC", affects_labs: ["HBA1C"] },
  "metformin":       { class: "BIGUANIDE", affects_labs: ["HBA1C"] }, // lowers A1c, useful context
  "insulin":         { class: "INSULIN", affects_labs: ["HBA1C"] },   // lowers A1c
};
```

If the team gives you additional medications to add, follow the same pattern. Do not invent drug classes.

---

## 8. The single LLM prompt (for `analyze_medication_lab_interactions` only)

This is the only place the system uses an LLM. Use it carefully.

**Model choice:** Use Codex (Codex-sonnet-4-6 or Codex-opus-4-7) via the Anthropic API. Set temperature to 0.2. Max tokens 800.

**System prompt:**
```
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
    { "medication": "<name>", "summary": "<1-2 sentences>" },
    ...
  ],
  "cumulative_risk_note": "<1-2 sentences>"
}
```

**User prompt template:**
```
Lab type: {LAB_TYPE}
Medications interacting with this lab:
{FOR each medication: "- {name} ({drug_class}, {direction})"}

Generate the JSON output as specified.
```

The MCP tool wraps this LLM call, validates the JSON output against a Zod schema, and merges the LLM's mechanism strings back into the structured output. **If the LLM output fails validation, return a fallback message and log a warning. Do not retry more than twice.**

---

## 9. Deterministic urgency rules (implement exactly)

These are demo-scaffolding rules. The team has approved them. Document each rule in code with a comment.

### Potassium (LOINC 2823-3)

```
IF current_value >= 6.0 mmol/L → URGENT
IF current_value >= 5.5 mmol/L AND (lab_trend = RISING OR has_significant_interactions) → URGENT
IF current_value >= 5.5 mmol/L → SOON
IF current_value >= 5.0 mmol/L AND has_significant_interactions → SOON
IF current_value >= 5.0 mmol/L → ROUTINE
IF current_value < 3.5 mmol/L → SOON  (hypokalemia, demo simplification)
ELSE → ROUTINE
```

Each rule that fires adds a line to `rule_trace` like: `"K+ >= 5.5 mmol/L AND medication interactions present → SOON elevated to URGENT"`.

### Creatinine (LOINC 2160-0) — note: ideally use eGFR, but keeping creatinine for demo simplicity

```
IF current_value > 2.0 mg/dL AND lab_trend = RISING → URGENT
IF current_value > 1.5 mg/dL AND delta_from_baseline >= 0.5 mg/dL → URGENT
IF current_value > 1.5 mg/dL AND has_significant_interactions → SOON
IF current_value > 1.5 mg/dL → SOON
IF lab_trend = RISING AND delta_from_baseline >= 0.3 mg/dL → SOON
ELSE → ROUTINE
```

### HbA1c (LOINC 4548-4)

```
IF current_value >= 10.0% → SOON  (not urgent — chronic, but needs intervention)
IF current_value >= 9.0% → SOON
IF current_value >= 7.0% AND patient has diabetes diagnosis → ROUTINE (above target, follow-up)
IF current_value >= 6.5% AND patient has NO diabetes diagnosis → SOON (new diagnosis territory)
ELSE → ROUTINE
```

HbA1c should NEVER be classified as URGENT in this demo. That's intentional — it shows the agent doesn't over-alert on chronic-disease findings.

---

## 10. The four synthetic patients (build these exactly)

Hand-author these as JSON FHIR Bundles in `data/synthetic_patients/`. Then write a setup script that POSTs them to the HAPI test FHIR server at startup. Each patient gets a UUID-based ID; record those IDs in a `data/synthetic_patients/MANIFEST.json` so the demo can reference them.

### Patient 1: "The medication-interaction wow moment" — URGENT case

- 68-year-old female
- Conditions: Stage 3b CKD (active), Hypertension (active), Heart failure with reduced EF (active)
- Active medications: Lisinopril 20 mg daily, Spironolactone 25 mg daily, Ibuprofen 400 mg TID (recently started), Furosemide 40 mg daily
- New lab: Potassium 6.1 mmol/L
- Prior potassium values: 5.4 mmol/L (3 weeks ago), 4.8 mmol/L (3 months ago)
- Expected output: URGENT, with rule trace showing the threshold rule, the rising trend, and the three interacting medications (ACE inhibitor + potassium-sparing diuretic + NSAID).
- Demo beat: "The agent identified three independent potassium-raising drugs coexisting in this patient's regimen. None of them alone would necessarily push K+ to 6.1, but the combination explains the magnitude."

### Patient 2: "Trend matters" — URGENT/SOON case

- 73-year-old male
- Conditions: Stage 3a CKD, Hypertension, Type 2 diabetes
- Active medications: Losartan 100 mg daily, Metformin 1000 mg BID, Naproxen 500 mg BID (started 2 weeks ago for back pain)
- New lab: Creatinine 2.1 mg/dL
- Prior creatinine values: 1.4 mg/dL (1 month ago), 1.3 mg/dL (6 months ago), 1.4 mg/dL (1 year ago)
- Expected output: URGENT, rule trace shows large delta from baseline, rising trend, NSAID + ARB combination.
- Demo beat: "Single result interpreted in context: this isn't 'mild renal impairment' — it's an acute change in a patient where two drugs (an ARB and an NSAID) work synergistically to compromise renal perfusion."

### Patient 3: "Don't over-alert" — SOON, not URGENT

- 55-year-old male
- Conditions: Type 2 diabetes (active, diagnosed 8 years ago), Hypertension
- Active medications: Metformin 1000 mg BID, Amlodipine 5 mg daily
- New lab: HbA1c 9.8%
- Prior HbA1c values: 9.2% (4 months ago), 8.8% (10 months ago)
- Last clinic visit: 5 months ago (missed scheduled 3-month follow-up)
- Expected output: SOON, rule trace explains chronic-disease management, no medication interactions raising A1c.
- Demo beat: "The agent correctly distinguishes between something that needs urgent response (potassium 6.1) and something that needs scheduled follow-up (poorly controlled A1c)."

### Patient 4: "Fail safe on missing data" — INSUFFICIENT_DATA

- 45-year-old female
- Conditions: None on problem list
- Active medications: None
- New lab: Potassium 5.3 mmol/L
- Prior potassium values: NONE (first lab in the system)
- Expected output: INSUFFICIENT_DATA, rule trace explains: borderline value, no trend data available, no medication context to refine assessment, recommend clinician review.
- Demo beat: "When the agent doesn't have enough information to be confident, it says so. It does not fabricate certainty."

These four patients map directly to the four demo scenes. Do not modify them without asking.

---

## 11. Repository structure

Build this exact structure. Don't add top-level directories without asking.

```
lablens/
├── README.md                          # Public-facing project description
├── LICENSE                            # MIT
├── .env.example                       # Documents required env vars (no secrets)
├── .gitignore
├── package.json
├── tsconfig.json
├── Dockerfile                         # For Cloud Run / container deployment
├── docker-compose.yml                 # For local dev
│
├── src/
│   ├── index.ts                       # MCP server entry point, JSON-RPC handler
│   ├── sharp/
│   │   ├── middleware.ts              # Reads X-FHIR-* headers into request context
│   │   └── context.ts                 # ContextVar / AsyncLocalStorage for per-request context
│   ├── fhir/
│   │   ├── client.ts                  # FHIR R4 REST client (uses SHARP context)
│   │   ├── queries.ts                 # Query builders for Condition, MedicationRequest, etc.
│   │   └── types.ts                   # FHIR resource type definitions (or use @types/fhir)
│   ├── tools/
│   │   ├── get_patient_context.ts
│   │   ├── get_lab_trend.ts
│   │   ├── analyze_medication_lab_interactions.ts
│   │   └── classify_lab_followup_urgency.ts
│   ├── clinical/
│   │   ├── drug_classes.ts            # The lookup table from section 7
│   │   ├── lab_loinc_codes.ts         # LOINC code constants
│   │   ├── urgency_rules.ts           # The deterministic rules from section 9
│   │   └── safety_disclaimers.ts      # Boilerplate safety strings
│   ├── llm/
│   │   ├── client.ts                  # Anthropic API client
│   │   ├── prompts.ts                 # The system prompt from section 8
│   │   └── schemas.ts                 # Zod schemas for LLM output validation
│   └── utils/
│       └── logging.ts                 # Structured logging (no PHI in logs)
│
├── test/
│   ├── tools/
│   │   ├── classify_urgency.test.ts   # Test every rule branch (target: 15-20 tests)
│   │   └── drug_classes.test.ts
│   ├── fixtures/
│   │   └── synthetic_responses/       # Mock FHIR responses for unit tests
│   └── integration/
│       └── end_to_end.test.ts         # Each of the 4 demo patients → expected output
│
├── data/
│   └── synthetic_patients/
│       ├── patient_001_urgent_potassium.json
│       ├── patient_002_creatinine_trend.json
│       ├── patient_003_a1c_chronic.json
│       ├── patient_004_insufficient_data.json
│       └── MANIFEST.json              # Maps patient names to FHIR IDs after upload
│
├── scripts/
│   ├── seed_fhir.ts                   # Uploads synthetic patients to HAPI FHIR server
│   ├── verify_marketplace.ts          # Sanity-check the published agent works
│   └── demo.ts                        # Runs all 4 demo patients in sequence (for video recording)
│
├── prompt_opinion/
│   ├── agent_config.md                # How the A2A agent is configured in the platform UI
│   ├── marketplace_description.md     # Public listing description
│   └── screenshots/                   # Of the agent running in the platform
│
└── demo/
    ├── demo_script.md                 # Beat-by-beat 3-minute video script
    └── recording_checklist.md         # Pre-recording sanity checks
```

---

## 12. Build order (this is the calendar)

We have 12 days. Today is day 1. Submission is day 12. You build in this order; do not reorder without asking.

| Days | Phase | Deliverable |
|---|---|---|
| 1–2 | **Platform de-risking** | A "hello world" MCP tool published to Prompt Opinion Marketplace. The team is responsible for the platform side; you support by giving them a minimal but functioning MCP server skeleton they can deploy and register. |
| 3 | **Repository scaffold** | Repo structure from section 11 created. README outlines the project. .env.example has all needed vars. Dockerfile builds. CI runs. |
| 4 | **Synthetic patients + FHIR seed** | The four JSON Bundles authored, `seed_fhir.ts` uploads them to HAPI test server, MANIFEST.json records IDs. Verify each patient is retrievable via FHIR GET. |
| 5 | **Deterministic core** | `classify_lab_followup_urgency` fully implemented, all rule branches unit-tested (15+ tests). `drug_classes.ts` complete with table from section 7. |
| 6 | **FHIR tools** | `get_patient_context` and `get_lab_trend` wired to FHIR via SHARP middleware. End-to-end test: given a synthetic patient ID, fetch their context and verify the structure matches the contract. |
| 7 | **LLM tool** | `analyze_medication_lab_interactions` working end-to-end. LLM prompt validated. Zod schemas reject malformed outputs. Test: each of the 4 patients produces a sensible mechanism narrative. |
| 8 | **Integration** | All four MCP tools registered on the server. A2A agent configured in Prompt Opinion to call them in sequence. End-to-end test: feed each of the 4 patients through the full pipeline, verify the output packet matches the expected demo beat. |
| 9 | **Demo polish** | Output formatting cleaned up. Rule traces are human-readable. Safety disclaimers in place. README polished. Marketplace listing written. |
| 10 | **Demo video** | Demo script (`demo/demo_script.md`) recorded. Under 3 minutes. Hosted publicly. |
| 11 | **Devpost write-up + dry run** | Devpost form filled out. Full dry run of the demo against the published marketplace agent. Final checks. |
| 12 (May 11) | **Submit by noon ET** | Submitted at noon as a safety margin against the 11pm deadline. |

If a phase slips, the team decides what to cut. **Default cuts in priority order:** Patient 4 (INSUFFICIENT_DATA case) → Patient 3 (HbA1c case) → trend analysis on creatinine. **Never cut:** Patient 1 (the wow moment) and the medication-interaction tool.

---

## 13. Testing requirements

- **Unit tests** for `classify_lab_followup_urgency`: every rule branch in section 9 must have at least one passing test. Target 15–20 tests minimum.
- **Unit tests** for `drug_classes` lookup: every entry in the table is matched correctly.
- **Integration tests**: each of the 4 synthetic patients runs through the full pipeline and produces the expected urgency tier + at least one expected rule trace string.
- **Snapshot tests** on the LLM tool's output structure (not exact text — Zod schema validation is enough).
- **Determinism check**: run the deterministic classifier 100 times on the same input; assert the output is byte-identical every time.

CI must run all tests on every commit. Do not merge to `main` with a red CI.

---

## 14. Logging and PHI policy

This is a hackathon, but treat it like production for PHI.

- **Never log** the contents of FHIR responses. Log only resource counts and timing.
- **Never log** LLM prompt inputs or outputs containing patient data.
- **Never log** the values of `X-FHIR-Access-Token` or any auth header.
- **Synthetic patient names** in synthetic data are FINE to log. They are not PHI. (e.g., "Patient_001_Urgent_Potassium" is fine.)
- Demo videos and screenshots use only the four synthetic patients defined in section 10.

If you find yourself wanting to log "for debugging," log a structured event with no payload (e.g., `{"event": "fhir_query_completed", "resource_type": "MedicationRequest", "result_count": 4}`).

---

## 15. The Devpost write-up (build a draft early)

Don't leave this for day 11. Draft it on day 9. The judges read the Devpost description before they watch the video; if your description is bad, the video doesn't get watched.

Required sections (Devpost asks for these explicitly):

1. **Inspiration** — 2 sentences. Lead with the "49 messages/day" stat. Mention that the bottleneck isn't reading labs, it's prioritizing them with full medication context.
2. **What it does** — 4 sentences. The one-sentence positioning + 3 sentences on the four-tool architecture.
3. **How we built it** — Architecture diagram, list of MCP tools, brief mention of SHARP/FHIR/Anthropic API.
4. **Challenges we ran into** — Be honest. Mention SHARP context propagation, FHIR query design, balancing deterministic vs LLM logic.
5. **Accomplishments we're proud of** — The medication-interaction tool, the deterministic-with-rule-traces design, full unit-test coverage of the classifier.
6. **What we learned** — One sentence on MCP, one on FHIR, one on agent orchestration.
7. **What's next for LabLens** — Expand to additional lab types, integrate with real FHIR-enabled EHRs, deploy in a stewardship pilot.

Tone: confident but not boastful. State facts. Don't oversell.

---

## 16. Things to ask the team before doing

These are NOT decisions for you to make alone. Stop and ask:

1. Before publishing anything to a public marketplace, confirm with the team that the agent name, description, and demo behavior are all what they want.
2. Before hard-coding any LLM API key, confirm the team's preferred provider (Anthropic vs OpenAI vs Gemini). Current default in this doc is Anthropic; verify.
3. Before adding any medication to the drug class table, confirm with the team. They have pharmacology references; you don't.
4. Before changing a deterministic rule threshold, confirm with the team.
5. Before adding any new tool beyond the four in section 6, confirm.
6. Before changing the synthetic patient data, confirm.
7. If a hackathon rule appears ambiguous (e.g., "is this hybrid MCP+A2A acceptable?"), the team should email the organizers; do not guess.

---

## 17. Hard rules — these never change

- Never use real PHI.
- Never message patients.
- Never autonomously place orders, prescriptions, referrals, or care actions.
- Never invent clinical thresholds, drug classes, or pharmacology mechanisms.
- Never ship with failing CI.
- Never log auth tokens or PHI.
- Always include "For clinician review only. Synthetic demo. Not autonomous medical advice." in every output packet.
- Always fail safely (return INSUFFICIENT_DATA) when inputs are incomplete.
- The LLM in `analyze_medication_lab_interactions` is the ONLY LLM call in the whole system. Do not add LLM calls elsewhere.

---

## 18. Reference URLs (already verified)

- Hackathon: https://agents-assemble.devpost.com/
- Hackathon rules: https://agents-assemble.devpost.com/rules
- Prompt Opinion platform: https://app.promptopinion.ai
- Prompt Opinion GitHub org: https://github.com/prompt-opinion
- po-community-mcp (default FHIR MCP, in C# — FOR REFERENCE ONLY, we are not extending this): https://github.com/prompt-opinion/po-community-mcp
- po-adk-typescript (the ADK we use): https://github.com/prompt-opinion/po-adk-typescript
- SHARP-on-MCP spec: https://sharponmcp.com
- MCP TypeScript SDK: https://github.com/modelcontextprotocol/typescript-sdk
- HAPI FHIR test server: https://hapi.fhir.org/baseR4
- Competitor (DO NOT REPLICATE): https://github.com/prabhakaran-jm/clinical-promise-keeper

---

## 19. Anti-patterns specifically observed in similar hackathon projects (avoid these)

These are real failure modes the team has observed in adjacent projects. Do not repeat them.

- **The "5-pass pipeline" trap.** Don't add LLM passes for "calibration," "verification," "narration," etc. We have one LLM call, deliberately. More passes = more places to hallucinate, more latency, more cost, harder demo.
- **The "dashboard for everything" trap.** Don't build a separate web dashboard. The demo runs inside Prompt Opinion's UI. A dashboard is a distraction.
- **The "F1 score on 21 notes" trap.** Don't try to validate clinical accuracy with a custom benchmark. Our validation is the four hand-crafted demo patients with expected outputs. That's enough for a hackathon.
- **The "8 specialties" trap.** Don't expand scope to additional labs or specialties to seem more impressive. Depth > breadth in a 3-minute demo.
- **The "we'll add OAuth ourselves" trap.** SHARP is explicit: the MCP server does NOT do OAuth. The agent host forwards the token. Read the spec.

---

## 20. First action

In order:

1. **Complete Section 0** (workspace pre-flight). This includes initializing Git, creating `.gitignore`, the stub README, the first commit, asking the team for the GitHub remote URL, verifying Node 20+, and creating `.env.example`. Do not skip any sub-step.
2. **Confirm with the team** that this document accurately reflects their plan. If they say yes, proceed. If they say "wait, we changed our mind on X," update the doc and recommit before coding.
3. **Browse the SHARP spec** at sharponmcp.com (3 short pages, ~15 minutes of reading). You don't need to memorize it — just understand the headers model.
4. **Re-read the Prompt Opinion Devpost rules** end-to-end (https://agents-assemble.devpost.com/rules) so you know exactly what counts as a valid submission.
5. **Scaffold the repo** per Section 11. Stub-level files are fine at this stage — empty `src/index.ts`, empty test file, etc. The point is the directory structure exists and `npm install` works.
6. **Get CI running** with one trivial passing test (e.g., `expect(1 + 1).toBe(2)`). Use GitHub Actions if the team has pushed to GitHub by now; skip CI if not — but make sure `npm test` passes locally.
7. **Commit and push.** "Scaffold project structure with passing CI."
8. **Then, and only then, start day-1 work**: a "hello world" MCP tool the team can publish to the Prompt Opinion Marketplace.

After step 8, the team takes over for the platform-side work (registering on Prompt Opinion, publishing the agent). You support by making sure the MCP server is reachable and the tool returns a sensible response.

---

*End of handoff document. Last updated: April 29, 2026. If you find this document contradicts itself or is missing information you need, stop and ask the team.*
