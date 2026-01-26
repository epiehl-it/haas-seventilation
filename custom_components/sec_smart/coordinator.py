from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SecSmartApi, SecSmartAuthError, SecSmartBadRequest
from .const import DOMAIN


class SecSmartCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: SecSmartApi,
        device_id: str,
        update_interval: timedelta,
    ) -> None:
        self.api = api
        self.device_id = device_id
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name=f"SEC Smart {device_id} areas",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            data = await self.api.async_get_areas(self.device_id)
        except SecSmartAuthError as err:
            raise UpdateFailed(f"Auth failed: {err}") from err
        except SecSmartBadRequest as err:
            raise UpdateFailed(f"Bad request: {err}") from err
        except Exception as err:  # pylint: disable=broad-except
            raise UpdateFailed(f"Unexpected error: {err}") from err

        # Normalize mode strings (strip) to cope with trailing spaces like "INACTIVE ".
        for area in data.values():
            if isinstance(area, dict) and "mode" in area and isinstance(area["mode"], str):
                area["mode"] = area["mode"].strip()
        return data
