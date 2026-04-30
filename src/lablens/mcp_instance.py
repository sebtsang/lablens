"""FastMCP server instance with `ai.promptopinion/fhir-context` capability and tool registry.

Tool registrations are intentionally stubs that raise NotImplementedError until
implemented per CLAUDE.md sections 6.1-6.4. The `ping` tool is the smoke-test
endpoint for verifying integration with the Prompt Opinion workspace; it will
be removed once `get_patient_context` is real.
"""

from typing import Any, cast

from mcp.server.fastmcp import Context, FastMCP

from lablens.fhir.utilities import get_fhir_context, get_patient_id_if_context_exists

mcp = FastMCP("LabLens", stateless_http=True, host="0.0.0.0")


_original_get_capabilities = cast("Any", mcp._mcp_server.get_capabilities)


def _patched_get_capabilities(
    notification_options: object, experimental_capabilities: object
) -> Any:
    caps = _original_get_capabilities(notification_options, experimental_capabilities)
    caps.model_extra["extensions"] = {
        "ai.promptopinion/fhir-context": {
            "scopes": [
                {"name": "patient/Patient.rs", "required": True},
                {"name": "patient/Observation.rs"},
                {"name": "patient/MedicationStatement.rs"},
                {"name": "patient/Condition.rs"},
                {"name": "offline_access"},
            ]
        }
    }
    return caps


mcp._mcp_server.get_capabilities = _patched_get_capabilities  # type: ignore[method-assign]


@mcp.tool(
    name="ping", description="Smoke-test tool: returns the SHARP context the server received."
)
def ping(ctx: Context) -> str:
    fhir_ctx = get_fhir_context(ctx)
    patient_id = get_patient_id_if_context_exists(ctx)
    if not fhir_ctx:
        return "pong (no FHIR context received)"
    return (
        f"pong | fhir_url={fhir_ctx.url} | "
        f"token={'present' if fhir_ctx.token else 'absent'} | "
        f"patient_id={patient_id or 'unset'}"
    )


# --- Stub tool registrations (per CLAUDE.md §6) ---
# Each tool below is a placeholder. Implementations land on D3-D5 of the calendar.


@mcp.tool(
    name="get_patient_context",
    description="Pull active conditions, medications, allergies, and recent encounters. See CLAUDE.md §6.1.",
)
def get_patient_context(ctx: Context) -> str:
    raise NotImplementedError("TODO: implement per CLAUDE.md §6.1")


@mcp.tool(
    name="get_lab_trend",
    description="Return recent values for a lab (by LOINC) and a coarse trend label. See CLAUDE.md §6.2.",
)
def get_lab_trend(ctx: Context, lab_loinc_code: str, lookback_months: int = 12) -> str:
    raise NotImplementedError("TODO: implement per CLAUDE.md §6.2")


@mcp.tool(
    name="analyze_medication_lab_interactions",
    description="Identify medications that interact with a given lab type and explain the mechanism. See CLAUDE.md §6.3.",
)
def analyze_medication_lab_interactions(
    ctx: Context,
    lab_type: str,
    active_medications: list[dict[str, str]],
) -> str:
    del lab_type
    raise NotImplementedError("TODO: implement per CLAUDE.md §6.3")


@mcp.tool(
    name="classify_lab_followup_urgency",
    description="Risk-stratify an incoming lab result deterministically. See CLAUDE.md §6.4.",
)
def classify_lab_followup_urgency(
    ctx: Context,
    lab_type: str,
    current_value: float,
    unit: str,
) -> str:
    del lab_type, current_value
    raise NotImplementedError("TODO: implement per CLAUDE.md §6.4")
