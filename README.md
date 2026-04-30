# LabLens

**Medication-aware lab triage agent for the Agents Assemble Healthcare AI Hackathon.**

LabLens turns an incoming abnormal lab result into a risk-stratified, medication-aware action packet for clinician review — combining deterministic threshold logic with LLM-driven pharmacology reasoning over the patient's active medication list.

- Submission deadline: May 11, 2026
- Marketplace: [app.promptopinion.ai](https://app.promptopinion.ai)
- Submission path: hybrid MCP server + no-code A2A agent inside Prompt Opinion's workspace

## What it does

Four MCP tools that work in sequence:

| Tool | Purpose |
|---|---|
| `get_patient_context` | Active conditions, medications (drug-class-enriched), allergies, encounters from FHIR |
| `get_lab_trend` | Recent values + RISING/FALLING/STABLE label for POTASSIUM, CREATININE, or HBA1C |
| `analyze_medication_lab_interactions` | Drug-class lookup + single Claude call for plain-language mechanism summaries (the AI Factor) |
| `classify_lab_followup_urgency` | Pure deterministic risk stratifier with transparent rule trace + safety disclaimer |

The headline demo case: 68-year-old female with CKD/HTN/HFrEF, on Lisinopril + Spironolactone + Ibuprofen + Furosemide, new K+ 6.1 → URGENT, with a rule trace naming all three potassium-raising drug classes.

## Stack

- Python 3.12 / FastMCP (in `mcp[cli]`)
- FastAPI + uvicorn (HTTP host)
- Pydantic v2 (validation)
- httpx async (FHIR client)
- One configurable LLM call site (mechanism narration only). Three backends supported via `LABLENS_LLM_PROVIDER`:
  - `gemini` (default) — `gemini-2.0-flash` via Google AI Studio (free)
  - `anthropic` — `claude-opus-4-7` (paid)
  - `ollama` — local `llama3.2` (free, offline)
- pytest + pytest-asyncio, Ruff, Pyright (standard mode), uv
- Railway (deployment, no Docker)

## Local development

```bash
# Install uv (https://docs.astral.sh/uv/) and sync
brew install uv
uv sync --extra dev

# Pick an LLM backend (default is Gemini)
export LABLENS_LLM_PROVIDER=gemini    # or "anthropic" or "ollama"
export GEMINI_API_KEY=...             # if using Gemini (free; aistudio.google.com)
# export ANTHROPIC_API_KEY=sk-ant-... # if using Anthropic
# (Ollama needs no key — just run `ollama serve` locally)

# Run the MCP server
uv run uvicorn lablens.server:app --reload --port 8000

# Healthcheck
curl http://127.0.0.1:8000/health

# MCP initialize (verifies capability advertisement)
curl -sX POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl","version":"0.1"}}}'
```

## Run the checks

```bash
uv run ruff check && uv run ruff format --check
uv run pyright
uv run pytest
```

## Connecting to Prompt Opinion

See [`prompt_opinion/agent_config.md`](./prompt_opinion/agent_config.md) for the no-code A2A agent setup (workspace, MCP server registration, agent configuration, smoke test, marketplace publishing).

## Repository layout

```
src/lablens/
├── server.py                      FastAPI host + lifespan + /health + /mcp mount
├── mcp_instance.py                FastMCP instance, capability advertisement, tool registry
├── mcp_constants.py               SHARP header names
├── fhir/
│   ├── client.py                  httpx async FHIR client
│   ├── context.py                 FhirContext dataclass
│   ├── queries.py                 fetch_patient_context, fetch_lab_trend (parsers + trend logic)
│   └── utilities.py               SHARP context extraction from request
├── tools/                         The four MCP tools
├── clinical/
│   ├── drug_classes.py            DRUG_CLASS_LOOKUP (CLAUDE.md §7)
│   ├── lab_loinc_codes.py         LOINC constants + LabType
│   ├── urgency_rules.py           Deterministic rules (CLAUDE.md §9)
│   ├── safety_disclaimers.py      SAFETY_LABEL
│   └── models.py                  Pydantic models (PatientContext, LabTrendResult, ...)
├── llm/
│   ├── client.py                  Anthropic call site with retries + Pydantic validation
│   ├── prompts.py                 System + user prompt (verbatim §8)
│   └── schemas.py                 LlmInteractionResponse
└── utils/
    └── logging.py                 (logging helpers — never logs PHI/tokens)
data/synthetic_patients/           Patient 1 FHIR Bundle + manifest
prompt_opinion/                    Platform configuration guide + marketplace listing copy
demo/                              Demo video script + recording checklist
tests/                             77 passing tests (clinical, tools, integration)
```

## Attribution

This project's MCP server scaffold (FastAPI + FastMCP wiring, capability advertisement, SHARP header context propagation, FHIR client patterns) is derived from [prompt-opinion/po-community-mcp](https://github.com/prompt-opinion/po-community-mcp), the reference healthcare MCP server that Prompt Opinion publishes as a starting point for hackathon participants.

## Project documentation

See [`CLAUDE.md`](./CLAUDE.md) for the full handoff document — clinical thresholds, drug-class table, urgency rules, synthetic patient specs, and the original 12-day calendar.

## License

MIT — see [`LICENSE`](./LICENSE).
