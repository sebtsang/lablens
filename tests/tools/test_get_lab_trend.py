"""Tests for fetch_lab_trend — Observation parsing + trend computation."""

from __future__ import annotations

from typing import cast

import pytest

from lablens.fhir.client import FhirClient
from lablens.fhir.queries import fetch_lab_trend
from tests.fixtures.fake_fhir_client import FakeFhirClient
from tests.fixtures.fhir_fixtures import empty_bundle, observation_bundle


@pytest.mark.asyncio
async def test_rising_trend_is_detected() -> None:
    # Most recent value >10% above the prior-3 median
    values = [
        (5.6, "2026-04-15"),
        (4.8, "2026-04-01"),
        (4.7, "2026-03-15"),
        (4.6, "2026-03-01"),
    ]
    fake = FakeFhirClient(
        searches={("Observation", frozenset()): observation_bundle(values)},
    )
    client = cast("FhirClient", fake)
    result = await fetch_lab_trend(client, "p-001", "POTASSIUM")
    assert result.trend == "RISING"
    assert result.delta_from_baseline is not None
    assert result.delta_from_baseline > 0


@pytest.mark.asyncio
async def test_falling_trend_is_detected() -> None:
    values = [
        (3.6, "2026-04-15"),
        (4.7, "2026-04-01"),
        (4.6, "2026-03-15"),
        (4.7, "2026-03-01"),
    ]
    fake = FakeFhirClient(
        searches={("Observation", frozenset()): observation_bundle(values)},
    )
    client = cast("FhirClient", fake)
    result = await fetch_lab_trend(client, "p-001", "POTASSIUM")
    assert result.trend == "FALLING"
    assert result.delta_from_baseline is not None
    assert result.delta_from_baseline < 0


@pytest.mark.asyncio
async def test_stable_trend_when_within_10_percent() -> None:
    values = [
        (4.8, "2026-04-15"),
        (4.7, "2026-04-01"),
        (4.8, "2026-03-15"),
        (4.6, "2026-03-01"),
    ]
    fake = FakeFhirClient(
        searches={("Observation", frozenset()): observation_bundle(values)},
    )
    client = cast("FhirClient", fake)
    result = await fetch_lab_trend(client, "p-001", "POTASSIUM")
    assert result.trend == "STABLE"


@pytest.mark.asyncio
async def test_insufficient_data_when_only_one_or_two_values() -> None:
    values = [(4.8, "2026-04-15"), (4.6, "2026-03-15")]
    fake = FakeFhirClient(
        searches={("Observation", frozenset()): observation_bundle(values)},
    )
    client = cast("FhirClient", fake)
    result = await fetch_lab_trend(client, "p-001", "POTASSIUM")
    assert result.trend == "INSUFFICIENT_DATA"
    assert result.delta_from_baseline is None


@pytest.mark.asyncio
async def test_empty_observation_bundle_is_insufficient_data() -> None:
    fake = FakeFhirClient(searches={("Observation", frozenset()): empty_bundle()})
    client = cast("FhirClient", fake)
    result = await fetch_lab_trend(client, "p-001", "POTASSIUM")
    assert result.trend == "INSUFFICIENT_DATA"
    assert result.values == []


@pytest.mark.asyncio
async def test_lab_metadata_matches_loinc_table() -> None:
    fake = FakeFhirClient(searches={("Observation", frozenset()): empty_bundle()})
    client = cast("FhirClient", fake)
    result = await fetch_lab_trend(client, "p-001", "CREATININE")
    assert result.lab_code == "2160-0"
    assert result.unit == "mg/dL"
    assert "Creatinine" in result.lab_display
