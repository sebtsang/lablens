"""SHARP FHIR context (URL + bearer token) extracted from request headers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FhirContext:
    url: str
    token: str | None = None
