from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

import api as api_module

BASE_URL = "https://api.example.test/v1"
DEVICE_ID = "1A2B3C"
TOKEN = "test-token"


@pytest.fixture
async def session():
    async with aiohttp.ClientSession() as s:
        yield s


@pytest.fixture
def api(session: aiohttp.ClientSession) -> api_module.SecSmartApi:
    return api_module.SecSmartApi(BASE_URL, TOKEN, session)


def _only_call(mocked: aioresponses):
    calls = [c for cs in mocked.requests.values() for c in cs]
    assert len(calls) == 1, f"expected exactly one HTTP call, got {len(calls)}"
    return calls[0]


async def test_get_areas_returns_parsed_json(api):
    payload = {
        "area1": {"label": "Kitchen", "mode": "Manual 3"},
        "area2": {"label": "Bathroom", "mode": "INACTIVE"},
    }
    with aioresponses() as m:
        m.get(f"{BASE_URL}/devices/{DEVICE_ID}/areas", payload=payload)
        result = await api.async_get_areas(DEVICE_ID)
    assert result == payload


async def test_get_areas_sends_bearer_token(api):
    with aioresponses() as m:
        m.get(f"{BASE_URL}/devices/{DEVICE_ID}/areas", payload={})
        await api.async_get_areas(DEVICE_ID)
        call = _only_call(m)
    assert call.kwargs["headers"]["Authorization"] == f"Bearer {TOKEN}"


async def test_set_area_mode_sends_expected_payload(api):
    with aioresponses() as m:
        m.put(f"{BASE_URL}/devices/{DEVICE_ID}/areas/mode", payload={})
        await api.async_set_area_mode(DEVICE_ID, 3, "Manual 4")
        call = _only_call(m)
    assert call.kwargs["json"] == {"areaid": 3, "mode": "Manual 4"}


async def test_set_area_mode_returns_none(api):
    with aioresponses() as m:
        m.put(f"{BASE_URL}/devices/{DEVICE_ID}/areas/mode", payload={})
        result = await api.async_set_area_mode(DEVICE_ID, 1, "Fans off")
    assert result is None


async def test_401_raises_auth_error(api):
    with aioresponses() as m:
        m.get(f"{BASE_URL}/devices/{DEVICE_ID}/areas", status=401)
        with pytest.raises(api_module.SecSmartAuthError):
            await api.async_get_areas(DEVICE_ID)


async def test_400_raises_bad_request_with_body(api):
    with aioresponses() as m:
        m.get(
            f"{BASE_URL}/devices/{DEVICE_ID}/areas",
            status=400,
            body="invalid syntax",
        )
        with pytest.raises(api_module.SecSmartBadRequest, match="invalid syntax"):
            await api.async_get_areas(DEVICE_ID)


async def test_5xx_raises_generic_aiohttp_error(api):
    with aioresponses() as m:
        m.get(f"{BASE_URL}/devices/{DEVICE_ID}/areas", status=503)
        with pytest.raises(aiohttp.ClientResponseError):
            await api.async_get_areas(DEVICE_ID)


async def test_base_url_trailing_slash_is_stripped(session):
    api = api_module.SecSmartApi(BASE_URL + "/", TOKEN, session)
    with aioresponses() as m:
        m.get(f"{BASE_URL}/devices/{DEVICE_ID}/areas", payload={})
        await api.async_get_areas(DEVICE_ID)
