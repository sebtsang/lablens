"""MCP tool: get_lab_trend (CLAUDE.md §6.2).

Returns recent values for a lab (by LabType) and a coarse RISING/FALLING/STABLE
trend label so the classifier can reason about acute change vs chronic state.
"""

from __future__ import annotations

from mcp.server.fastmcp import Context

from lablens.clinical.lab_loinc_codes import LabType
from lablens.clinical.models import LabTrendResult
from lablens.fhir.client import FhirClient
from lablens.fhir.queries import fetch_lab_trend
from lablens.fhir.utilities import get_fhir_context, get_patient_id_if_context_exists


async def run(  # type: ignore[type-arg]
    ctx: Context,
    lab_type: LabType,
    lookback_months: int = 12,
    patient_id: str | None = None,
) -> LabTrendResult:
    fhir_ctx = get_fhir_context(ctx)
    if fhir_ctx is None:
        raise ValueError("FHIR context missing — X-FHIR-Server-URL header not received")
    resolved_patient_id = patient_id or get_patient_id_if_context_exists(ctx)
    if not resolved_patient_id:
        raise ValueError("No patient context found — provide patient_id or X-Patient-ID header")
    client = FhirClient(base_url=fhir_ctx.url, token=fhir_ctx.token)
    return await fetch_lab_trend(
        client, resolved_patient_id, lab_type, lookback_months=lookback_months
    )
