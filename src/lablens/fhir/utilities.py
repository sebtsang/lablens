"""Extract SHARP FHIR context and patient ID from the per-request MCP context."""

from typing import Any

import jwt
from mcp.server.fastmcp import Context

from lablens.fhir.context import FhirContext
from lablens.mcp_constants import (
    FHIR_ACCESS_TOKEN_HEADER,
    FHIR_SERVER_URL_HEADER,
    PATIENT_ID_HEADER,
)


def _request_headers(ctx: Context) -> dict[str, str] | None:  # type: ignore[type-arg]
    request = ctx.request_context.request
    if request is None:
        return None
    headers: Any = request.headers
    return headers


def get_fhir_context(ctx: Context) -> FhirContext | None:  # type: ignore[type-arg]
    headers = _request_headers(ctx)
    if headers is None:
        return None
    url = headers.get(FHIR_SERVER_URL_HEADER)
    if not url:
        return None
    token = headers.get(FHIR_ACCESS_TOKEN_HEADER)
    return FhirContext(url=url, token=token)


def get_patient_id_if_context_exists(ctx: Context) -> str | None:  # type: ignore[type-arg]
    headers = _request_headers(ctx)
    if headers is None:
        return None
    fhir_token = headers.get(FHIR_ACCESS_TOKEN_HEADER)
    if fhir_token:
        claims: dict[str, Any] = jwt.decode(fhir_token, options={"verify_signature": False})
        patient = claims.get("patient")
        if patient:
            return str(patient)
    return headers.get(PATIENT_ID_HEADER)
