# Devpost submission draft

Per hackathon rules §4, the Devpost form expects: Inspiration, What it does, How we built it, Challenges we ran into, Accomplishments we're proud of, What we learned, What's next for LabLens. Plus the project URL (Marketplace), the demo video URL, and the GitHub repo URL. This file is the draft to paste into Devpost on D11.

---

## Inspiration

Clinicians receive 49 to 56 EHR inbox messages per day in published studies, and 6.8% to 62% of abnormal lab results have documented missed follow-up. The bottleneck isn't *reading* a lab — it's prioritizing dozens of them while assembling the patient-specific medication context that determines whether a given result is an emergency or a routine finding. A potassium of 6.1 mmol/L is concerning in any patient, but in a patient on lisinopril + spironolactone + ibuprofen — three independent potassium-raising drugs — it's significantly more dangerous. That medication-context synthesis is exactly what an LLM does well and exactly what a rule-engine alert system cannot.

## What it does

LabLens turns an incoming abnormal lab result into a risk-stratified, medication-aware action packet for clinician review. It exposes four MCP tools that work in sequence: pull the patient's active conditions and medications from FHIR; pull recent values for the lab to compute a trend; identify which of the patient's medications interact with the lab type and explain the mechanisms with a single LLM call; classify urgency deterministically with a transparent rule trace. The clinician sees urgency (URGENT / SOON / ROUTINE / INSUFFICIENT_DATA), the rule trace, the patient's risk factors, a recommended review path, and a mandatory safety disclaimer.

## How we built it

- **MCP server**: Python 3.12 + FastMCP, deployed to Railway. Mounts at `POST /mcp` with streamable HTTP transport. Advertises the `ai.promptopinion/fhir-context` capability with the standard SHARP scopes.
- **SHARP context propagation**: per-request reader for `X-FHIR-Server-URL`, `X-FHIR-Access-Token`, `X-Patient-ID`. The server forwards the bearer token on outbound FHIR calls but never logs or persists it.
- **Validation**: Pydantic v2 models for every tool's input and output shape, including the LLM JSON output.
- **The differentiator**: `analyze_medication_lab_interactions` uses a deterministic drug-class lookup (validated against pharmacology references) followed by one constrained LLM call to generate plain-language mechanism summaries. The deployed backend can use Gemini by default or Anthropic when configured; either way, the LLM is constrained to mechanism narration and cannot add medications or invent drug classes.
- **The classifier**: pure deterministic Python. Same inputs always produce same outputs. Every rule branch is unit-tested. Fails safe to INSUFFICIENT_DATA when inputs are incomplete.
- **Submission path**: Path A (MCP server) plus a no-code A2A agent configured inside Prompt Opinion's workspace builder.

Architecture and patterns derived from `prompt-opinion/po-community-mcp` (the official Prompt Opinion reference) with attribution. SHARP-on-MCP spec at sharponmcp.com.

## Challenges we ran into

- **SHARP context propagation in a streamable HTTP server.** The pattern is documented but ergonomic only after you've read the reference implementation; we spent more time figuring out where the request headers live in the FastMCP context than writing the actual tool logic.
- **Balancing deterministic logic with LLM reasoning.** The temptation is to let the LLM do everything. We deliberately constrained it: the LLM only narrates mechanisms for medication-lab interactions that the deterministic step already identified. This makes the demo reproducible and the urgency classification auditable.
- **Demoing inside Prompt Opinion vs. locally.** The judging gate (Stage 1) requires the agent to be invokable inside the platform, not just our server running in isolation. That meant authoring synthetic patients as FHIR transaction Bundles uploadable to a workspace and configuring a no-code A2A agent in the platform UI to chain our four tools.
- **Scope discipline.** It would have been easy to add labs, specialties, or LLM passes "to seem more impressive." We held the line at three labs (POTASSIUM, CREATININE, HBA1C) and one LLM call. Depth over breadth.

## Accomplishments we're proud of

- **The medication-interaction tool genuinely demonstrates the AI factor.** Three potassium-raising drug classes coexisting in one patient's regimen is exactly the synthesis a rule engine can't do. The demo case (Patient 1) lands cleanly: K+ 6.1 with ACE inhibitor + potassium-sparing diuretic + NSAID + furosemide produces an URGENT classification with a rule trace that names all three contributing drug classes.
- **Deterministic-with-rule-traces design.** Every classification carries a human-readable list of which rules fired and why. Clinicians can audit any decision. We unit-test every rule branch.
- **Fail-safe behavior.** When trend data is missing AND no medication interactions are identified AND the value is borderline, the agent returns INSUFFICIENT_DATA rather than guessing. This is a feature, not a limitation.
- **80 passing tests** including end-to-end integration tests across all four synthetic FHIR bundles.

## What we learned

- **MCP**: how custom HTTP headers thread through a streamable transport; how to advertise platform-specific capabilities; how to expose tools that compose cleanly.
- **FHIR**: the variability in how servers encode optional fields and why permissive parsing matters for production-grade integration.
- **Agent orchestration**: when to give the LLM autonomy (mechanism narration, framed and constrained) and when to keep it out of the loop (urgency classification, where determinism is non-negotiable).

## What's next for LabLens

- Expand to additional labs and drug classes once the team's pharmacology validation extends past the current three.
- Integrate with real FHIR-enabled EHRs through SHARP-aware launch contexts.
- Pilot in a stewardship workflow where clinicians review the triaged packets and feed back on the rule traces.

---

## Required form fields

| Field | Value |
|---|---|
| Project name | LabLens |
| Tagline | Medication-aware lab triage for clinician review |
| Marketplace URL | (fill in after publishing) |
| Demo video URL | (fill in after recording on D10) |
| GitHub repo | https://github.com/sebtsang/lablens |
| Tech tags | python, fastapi, fastmcp, anthropic, claude, fhir, mcp, healthcare-ai, sharp, prompt-opinion |

## Submission integrity check (rules §4)

- [x] Path A (MCP server) — confirmed
- [x] Synthetic data only — Patient 1 is hand-authored; built-in patients are de-identified samples
- [x] No real PHI in repo, video, or description
- [ ] Marketplace listing published and discoverable (D9)
- [ ] Demo video < 3 min, public on YouTube (D10)
- [ ] GitHub repo public with MIT license (already done)
