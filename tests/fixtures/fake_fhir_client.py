"""In-memory fake FhirClient used to exercise the query layer without HTTP."""

from __future__ import annotations

from typing import Any


class FakeFhirClient:
    """Stub matching the FhirClient surface (read + search) for tests."""

    def __init__(
        self,
        *,
        reads: dict[str, dict[str, Any] | None] | None = None,
        searches: dict[tuple[str, frozenset[tuple[str, str]]], dict[str, Any] | None] | None = None,
    ) -> None:
        self._reads = reads or {}
        self._searches = searches or {}

    async def read(self, path: str) -> dict[str, Any] | None:
        return self._reads.get(path)

    async def search(
        self, resource_type: str, search_parameters: dict[str, str] | None = None
    ) -> dict[str, Any] | None:
        key = (resource_type, frozenset((search_parameters or {}).items()))
        if key in self._searches:
            return self._searches[key]
        # Fallback: match by resource_type only (lets tests skip exact param matching)
        for (rt, _), bundle in self._searches.items():
            if rt == resource_type:
                return bundle
        return None
