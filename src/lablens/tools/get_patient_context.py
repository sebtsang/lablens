"""MCP tool: get_patient_context (CLAUDE.md §6.1).

Reads SHARP context (FHIR URL + token + patient ID) from the per-request MCP
context, queries the FHIR server for active conditions, medications, allergies,
and recent encounters, and returns a PatientContext model.
"""

from __future__ import annotations

from mcp.server.fastmcp import Context

from lablens.clinical.models import PatientContext
from lablens.fhir.client import FhirClient
from lablens.fhir.queries import fetch_patient_context
from lablens.fhir.utilities import get_fhir_context, get_patient_id_if_context_exists


async def run(ctx: Context, patient_id: str | None = None) -> PatientContext:  # type: ignore[type-arg]
    fhir_ctx = get_fhir_context(ctx)
    if fhir_ctx is None:
        raise ValueError("FHIR context missing — X-FHIR-Server-URL header not received")
    resolved_patient_id = patient_id or get_patient_id_if_context_exists(ctx)
    if not resolved_patient_id:
        raise ValueError("No patient context found — provide patient_id or X-Patient-ID header")
    client = FhirClient(base_url=fhir_ctx.url, token=fhir_ctx.token)
    return await fetch_patient_context(client, resolved_patient_id)
