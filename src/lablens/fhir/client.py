"""Async FHIR R4 REST client. Forwards the SHARP-supplied bearer token on every call."""

from typing import Any

import httpx


class FhirClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _build_url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any] | None:
        headers: dict[str, str] = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        async with httpx.AsyncClient() as client:
            response = await client.get(self._build_url(path), headers=headers, params=params)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def read(self, path: str) -> dict[str, Any] | None:
        return await self._get(path)

    async def search(
        self,
        resource_type: str,
        search_parameters: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        return await self._get(resource_type, params=search_parameters)
