"""FastMCP server instance with the four LabLens tools and the SHARP capability advertisement.

Each tool wraps the underlying implementation in `lablens.tools.*`, threading the
SHARP context (FHIR URL + token + patient ID) through where needed. The MCP-facing
signatures use simple types so the JSON-RPC schema is clean for Prompt Opinion's
agent builder; complex inputs (PatientContext, LabTrendResult, MedicationInteractions)
are deserialized via Pydantic inside each tool.
"""

from typing import Annotated, Any, cast

from anthropic import Anthropic
from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field

from lablens.clinical.lab_loinc_codes import LabType
from lablens.clinical.models import (
    LabTrendResult,
    MedicationInteractions,
    MedicationRef,
    PatientContext,
)
from lablens.tools.analyze_medication_lab_interactions import run as analyze_run
from lablens.tools.classify_lab_followup_urgency import classify
from lablens.tools.get_lab_trend import run as get_lab_trend_run
from lablens.tools.get_patient_context import run as get_patient_context_run

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
                {"name": "patient/MedicationRequest.rs"},
                {"name": "patient/Condition.rs"},
                {"name": "patient/Encounter.rs"},
                {"name": "patient/AllergyIntolerance.rs"},
                {"name": "offline_access"},
            ]
        }
    }
    return caps


mcp._mcp_server.get_capabilities = _patched_get_capabilities  # type: ignore[method-assign]


# ---------------------------------------------------------------------------
# Tool registrations (CLAUDE.md §6.1-§6.4)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="get_patient_context",
    description=(
        "Pull the patient's active conditions, active medications, allergies, and "
        "recent encounters from FHIR. Reads SHARP context from request headers."
    ),
)
async def get_patient_context(
    ctx: Context,  # type: ignore[type-arg]
    patient_id: Annotated[
        str | None, Field(description="Optional patient id; falls back to X-Patient-ID header.")
    ] = None,
) -> dict[str, Any]:
    result: PatientContext = await get_patient_context_run(ctx, patient_id=patient_id)
    return result.model_dump()


@mcp.tool(
    name="get_lab_trend",
    description=(
        "Return recent values for a specific lab (POTASSIUM, CREATININE, or HBA1C) and "
        "a coarse RISING/FALLING/STABLE/INSUFFICIENT_DATA trend label."
    ),
)
async def get_lab_trend(
    ctx: Context,  # type: ignore[type-arg]
    lab_type: Annotated[LabType, Field(description="One of POTASSIUM, CREATININE, HBA1C.")],
    lookback_months: Annotated[int, Field(description="How far back to look. Default 12.")] = 12,
    patient_id: Annotated[
        str | None, Field(description="Optional patient id; falls back to X-Patient-ID header.")
    ] = None,
) -> dict[str, Any]:
    result: LabTrendResult = await get_lab_trend_run(
        ctx, lab_type=lab_type, lookback_months=lookback_months, patient_id=patient_id
    )
    return result.model_dump()


@mcp.tool(
    name="analyze_medication_lab_interactions",
    description=(
        "Identify medications that interact with a given lab type (POTASSIUM, CREATININE, HBA1C) "
        "and return a structured interaction list with plain-language mechanism summaries. "
        "This is the only LLM-backed tool — uses Claude for mechanism narration only. "
        "REQUIRED PARAMETERS: lab_type (str), active_medications (list of medication dicts). "
        "Pass the active_medications field from get_patient_context's output verbatim — do not "
        "omit it or call this tool before get_patient_context has returned medications."
    ),
)
def analyze_medication_lab_interactions(
    lab_type: Annotated[LabType, Field(description="One of POTASSIUM, CREATININE, HBA1C.")],
    active_medications: Annotated[
        list[dict[str, Any]],
        Field(
            description=(
                "List of active medications, each as the active_medications shape "
                "from get_patient_context."
            )
        ),
    ],
) -> dict[str, Any]:
    parsed = [MedicationRef.model_validate(m) for m in active_medications]
    result: MedicationInteractions = analyze_run(
        lab_type, parsed, anthropic_client=cast("Anthropic | None", None)
    )
    return result.model_dump()


def _coerce_patient_context(raw: dict[str, Any]) -> PatientContext:
    """Build a PatientContext from whatever shape the orchestrator passes.

    Orchestrator LLMs often reconstruct prior tool outputs imperfectly — fields
    get omitted, types get loosened, or the structure gets flattened. We extract
    the minimal fields the classifier actually consumes (active_conditions for
    HbA1c diabetes detection) and fill the rest with safe defaults so validation
    never blocks on cosmetic shape differences.
    """
    try:
        return PatientContext.model_validate(raw)
    except Exception:
        pass
    demo_raw = raw.get("demographics") if isinstance(raw, dict) else None
    if not isinstance(demo_raw, dict):
        demo_raw = {}
    age = demo_raw.get("age", 0)
    if not isinstance(age, int):
        try:
            age = int(age)
        except (TypeError, ValueError):
            age = 0
    sex = str(demo_raw.get("sex", "unknown"))
    conditions: list[dict[str, Any]] = []
    raw_conds = raw.get("active_conditions") if isinstance(raw, dict) else None
    if isinstance(raw_conds, list):
        for c in raw_conds:
            if isinstance(c, dict):
                conditions.append(
                    {"code": str(c.get("code", "")), "display": str(c.get("display", ""))}
                )
            elif isinstance(c, str):
                conditions.append({"code": "", "display": c})
    return PatientContext(
        patient_id=str(raw.get("patient_id", "")) if isinstance(raw, dict) else "",
        demographics={"age": age, "sex": sex},  # type: ignore[arg-type]
        active_conditions=conditions,  # type: ignore[arg-type]
    )


def _coerce_lab_trend(raw: dict[str, Any]) -> LabTrendResult:
    try:
        return LabTrendResult.model_validate(raw)
    except Exception:
        pass
    if not isinstance(raw, dict):
        raw = {}
    trend = raw.get("trend", "INSUFFICIENT_DATA")
    if trend not in ("RISING", "FALLING", "STABLE", "INSUFFICIENT_DATA"):
        trend = "INSUFFICIENT_DATA"
    delta = raw.get("delta_from_baseline")
    if delta is not None:
        try:
            delta = float(delta)
        except (TypeError, ValueError):
            delta = None
    return LabTrendResult(
        lab_code=str(raw.get("lab_code", "")),
        lab_display=str(raw.get("lab_display", "")),
        unit=str(raw.get("unit", "")),
        values=[],
        trend=trend,  # type: ignore[arg-type]
        delta_from_baseline=delta,
    )


def _coerce_medication_interactions(raw: dict[str, Any]) -> MedicationInteractions:
    try:
        return MedicationInteractions.model_validate(raw)
    except Exception:
        pass
    if not isinstance(raw, dict):
        raw = {}
    has_sig = bool(raw.get("has_significant_interactions", False))
    note = str(raw.get("cumulative_risk_note", "Cumulative risk note unavailable."))
    return MedicationInteractions(
        interactions_found=[],
        cumulative_risk_note=note,
        has_significant_interactions=has_sig,
    )


@mcp.tool(
    name="classify_lab_followup_urgency",
    description=(
        "Risk-stratify an incoming lab result deterministically. Returns urgency "
        "(URGENT/SOON/ROUTINE/INSUFFICIENT_DATA), a transparent rule trace, risk "
        "factors, recommended review path, and a mandatory safety disclaimer. "
        "REQUIRED PARAMETERS: lab_type, current_value, unit, patient_context, lab_trend, "
        "medication_interactions. Pass patient_context (from get_patient_context), lab_trend "
        "(from get_lab_trend), and medication_interactions (from analyze_medication_lab_interactions) "
        "as the verbatim outputs of those prior tool calls — they are required, not optional."
    ),
)
def classify_lab_followup_urgency(
    lab_type: Annotated[LabType, Field(description="POTASSIUM, CREATININE, or HBA1C.")],
    current_value: Annotated[float, Field(description="The new lab value.")],
    unit: Annotated[str, Field(description="Unit of the value (e.g., 'mmol/L').")],
    patient_context: Annotated[dict[str, Any], Field(description="Output of get_patient_context.")],
    lab_trend: Annotated[dict[str, Any], Field(description="Output of get_lab_trend.")],
    medication_interactions: Annotated[
        dict[str, Any], Field(description="Output of analyze_medication_lab_interactions.")
    ],
) -> dict[str, Any]:
    result = classify(
        lab_type=lab_type,
        current_value=current_value,
        unit=unit,
        patient_context=_coerce_patient_context(patient_context),
        lab_trend=_coerce_lab_trend(lab_trend),
        medication_interactions=_coerce_medication_interactions(medication_interactions),
    )
    return result.model_dump()
