from __future__ import annotations

from typing import Any, Dict, Optional

import aiohttp


class SecSmartApi:
    def __init__(self, base_url: str, token: str, session: aiohttp.ClientSession) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._session = session

    async def _request(self, method: str, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._token}"}
        async with self._session.request(method, url, headers=headers, json=json, timeout=20) as resp:
            if resp.status == 401:
                raise SecSmartAuthError("Unauthorized (401)")
            if resp.status == 400:
                detail = await resp.text()
                raise SecSmartBadRequest(f"Bad Request (400): {detail}")
            resp.raise_for_status()
            if resp.content_type == "application/json":
                return await resp.json()
            return await resp.text()

    async def async_get_areas(self, device_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"/devices/{device_id}/areas")

    async def async_set_area_mode(self, device_id: str, area_id: int, mode: str) -> None:
        payload = {"areaid": area_id, "mode": mode}
        await self._request("PUT", f"/devices/{device_id}/areas/mode", json=payload)


class SecSmartError(Exception):
    """Base error for SEC Smart API."""


class SecSmartAuthError(SecSmartError):
    """Authentication failed."""


class SecSmartBadRequest(SecSmartError):
    """400 from API."""
