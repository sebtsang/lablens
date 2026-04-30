# LabLens

A medication-aware lab triage agent for the Agents Assemble Healthcare AI Hackathon.

LabLens turns an incoming abnormal lab result into a risk-stratified, medication-aware action packet for clinician review — by combining deterministic threshold logic with LLM-driven pharmacology reasoning over the patient's active medication list.

**Status:** Under active development.
**Hackathon submission deadline:** May 11, 2026.
**Marketplace:** [app.promptopinion.ai](https://app.promptopinion.ai)

## Stack

- Python 3.12+ with [FastMCP](https://github.com/modelcontextprotocol/python-sdk) (MCP server framework)
- FastAPI + uvicorn (HTTP host)
- Pydantic v2 (validation)
- httpx (async FHIR client)
- Anthropic SDK with `claude-opus-4-7` (single LLM call for medication-interaction narration)
- Pytest, Ruff, Pyright (strict)
- uv (package manager)
- Railway (deployment)

## Local development

```bash
# Install uv (https://docs.astral.sh/uv/)
brew install uv

# Sync dependencies
uv sync --extra dev

# Run the server locally on port 8000
uv run uvicorn lablens.server:app --reload --port 8000

# Run checks
uv run ruff check
uv run ruff format --check
uv run pyright
uv run pytest
```

## Attribution

This project's MCP server scaffold (FastAPI + FastMCP wiring, capability advertisement, SHARP header context propagation) was derived from the patterns in [prompt-opinion/po-community-mcp](https://github.com/prompt-opinion/po-community-mcp), the reference healthcare MCP server published by Prompt Opinion as a starting point for hackathon participants.

## Project documentation

See [`CLAUDE.md`](./CLAUDE.md) for the full project plan, architecture notes, clinical content, and 12-day calendar.

## License

MIT — see [`LICENSE`](./LICENSE).
