from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict
import logging
from pathlib import Path

import voluptuous as vol
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import SecSmartApi
from .const import (
    CONF_BASE_URL,
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_POLL_INTERVAL,
    DEFAULT_BASE_URL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)
from .coordinator import SecSmartCoordinator

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_DEVICES): vol.All(
                    vol.Length(min=1),
                    [
                        vol.Schema(
                            {
                                vol.Required(CONF_DEVICE_ID): str,
                                vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.Coerce(int),
                            }
                        )
                    ],
                ),
                vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.Coerce(int),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    if DOMAIN not in config:
        return True

    cfg = config[DOMAIN]
    base_url: str = cfg.get(CONF_BASE_URL, DEFAULT_BASE_URL)
    token: str = cfg[CONF_TOKEN]
    default_interval: int = cfg.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)

    session = async_get_clientsession(hass)
    api = SecSmartApi(base_url, token, session)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["api"] = api
    hass.data[DOMAIN].setdefault("coordinators", {})

    for device_cfg in cfg[CONF_DEVICES]:
        device_id = device_cfg[CONF_DEVICE_ID]
        interval = device_cfg.get(CONF_POLL_INTERVAL, default_interval)
        coordinator = SecSmartCoordinator(
            hass,
            api,
            device_id,
            update_interval=timedelta(seconds=interval),
        )
        await coordinator.async_refresh()

        hass.data[DOMAIN]["coordinators"][device_id] = coordinator

        discovery_info: Dict[str, Any] = {
            "device_id": device_id,
        }
        hass.async_create_task(
            discovery.async_load_platform(
                hass,
                "fan",
                DOMAIN,
                discovery_info,
                config,
            )
        )

    await _ensure_card_installed(hass)

    return True


async def _ensure_card_installed(hass: HomeAssistant) -> None:
    """Kopiert die Custom Card ins www-Verzeichnis, damit /local/... funktioniert."""
    src = Path(__file__).resolve().parents[2] / "www" / "sec-smart-fan-card.js"
    if not src.exists():
        _LOGGER.debug("SEC Smart card source not found at %s", src)
        return

    dest_dir = Path(hass.config.config_dir).joinpath("www")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir.joinpath("sec-smart-fan-card.js")

    def _copy():
        try:
            _LOGGER.info("Copying SEC Smart card to %s", dest)
            dest.write_bytes(src.read_bytes())
        except Exception as err:  # pragma: no cover - best effort
            _LOGGER.warning("Could not copy SEC Smart card: %s", err)

    await hass.async_add_executor_job(_copy)
