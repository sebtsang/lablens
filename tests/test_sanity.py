"""Sanity test so CI is green from day 1. Removed once real tests land on D3."""

from lablens import mcp_constants


def test_arithmetic_sanity() -> None:
    assert 1 + 1 == 2


def test_sharp_header_constants_match_spec() -> None:
    assert mcp_constants.FHIR_SERVER_URL_HEADER == "x-fhir-server-url"
    assert mcp_constants.FHIR_ACCESS_TOKEN_HEADER == "x-fhir-access-token"
    assert mcp_constants.PATIENT_ID_HEADER == "x-patient-id"
