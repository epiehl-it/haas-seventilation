from __future__ import annotations

from typing import Any, Dict, Optional

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .api import SecSmartApi, SecSmartError
from .const import (
    DOMAIN,
    MANUAL_PERCENTAGES,
    PRESET_BOOST,
    PRESET_CO2,
    PRESET_HUMIDITY,
    PRESET_INACTIVE,
    PRESET_SCHEDULE,
    PRESET_SLEEP,
    SUPPORTED_PRESETS,
)
from .coordinator import SecSmartCoordinator

# HA will call async_setup_platform because we load the platform via discovery


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    if discovery_info is None:
        return

    device_id = discovery_info["device_id"]
    api: SecSmartApi = hass.data[DOMAIN]["api"]
    coordinator: SecSmartCoordinator = hass.data[DOMAIN]["coordinators"][device_id]

    entities: list[SecSmartAreaFan] = []
    areas: Dict[str, Any] = coordinator.data or {}

    for idx in range(1, 7):
        area_key = f"area{idx}"
        area_data = areas.get(area_key)
        if not area_data:
            continue
        mode = (area_data.get("mode") or "").strip()
        if mode.upper().startswith("INACTIVE"):
            continue  # Skip inactive areas
        entities.append(
            SecSmartAreaFan(
                api=api,
                coordinator=coordinator,
                device_id=device_id,
                area_id=idx,
            )
        )

    if entities:
        async_add_entities(entities)


class SecSmartAreaFan(FanEntity):
    _attr_should_poll = False
    _attr_supported_features = FanEntityFeature.SET_PERCENTAGE | FanEntityFeature.PRESET_MODE
    _attr_preset_modes = SUPPORTED_PRESETS

    def __init__(
        self,
        api: SecSmartApi,
        coordinator: SecSmartCoordinator,
        device_id: str,
        area_id: int,
    ) -> None:
        self.api = api
        self.coordinator = coordinator
        self.device_id = device_id
        self.area_id = area_id
        self._attr_unique_id = f"{device_id}_area{area_id}"
        self._attr_name = self._derive_name()

    @property
    def available(self) -> bool:
        data = self._area_data
        mode = (data.get("mode") or "").strip() if data else ""
        return not mode.upper().startswith("INACTIVE")

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            manufacturer="SEC",
            name=f"SEC Smart {self.device_id}",
        )

    @property
    def _area_data(self) -> Dict[str, Any]:
        return (self.coordinator.data or {}).get(f"area{self.area_id}", {})

    def _derive_name(self) -> str:
        label = (self._area_data.get("label") or f"Area {self.area_id}").strip()
        return label or f"Area {self.area_id}"

    @property
    def name(self) -> str:
        return self._derive_name()

    @property
    def percentage(self) -> Optional[int]:
        mode = (self._area_data.get("mode") or "").strip()
        if mode.startswith("Manual"):
            try:
                level = int(mode.split()[1])
                return MANUAL_PERCENTAGES.get(level)
            except Exception:
                return None
        if mode == "Fans off":
            return 0
        if mode == "Boost ventilation":
            return 100
        return None

    @property
    def preset_mode(self) -> Optional[str]:
        mode = (self._area_data.get("mode") or "").strip()
        if mode == "Boost ventilation":
            return PRESET_BOOST
        if mode == "Humidity regulation":
            return PRESET_HUMIDITY
        if mode == "CO2 regulation":
            return PRESET_CO2
        if mode == "Timed program":
            return PRESET_SCHEDULE
        if mode == "Snooze":
            return PRESET_SLEEP
        if mode.upper().startswith("INACTIVE"):
            return PRESET_INACTIVE
        return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        attrs: Dict[str, Any] = {}
        area = self._area_data
        timers = area.get("timers")
        if timers:
            attrs["timers"] = timers
        return attrs

    async def async_set_percentage(self, percentage: int) -> None:
        # Map to nearest manual stage.
        level = _percentage_to_level(percentage)
        await self._set_mode(f"Manual {level}")

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        mode = preset_mode
        if preset_mode == PRESET_BOOST:
            mode = "Boost ventilation"
        elif preset_mode == PRESET_HUMIDITY:
            mode = "Humidity regulation"
        elif preset_mode == PRESET_CO2:
            mode = "CO2 regulation"
        elif preset_mode == PRESET_SCHEDULE:
            mode = "Timed program"
        elif preset_mode == PRESET_SLEEP:
            mode = "Snooze"
        elif preset_mode == PRESET_INACTIVE:
            mode = "INACTIVE"
        else:
            return
        await self._set_mode(mode)

    async def async_turn_on(self, percentage: Optional[int] = None, preset_mode: Optional[str] = None, **kwargs: Any) -> None:
        if preset_mode:
            await self.async_set_preset_mode(preset_mode)
            return
        if percentage is None:
            percentage = 50
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set_mode("Fans off")

    async def _set_mode(self, mode: str) -> None:
        await self.api.async_set_area_mode(self.device_id, self.area_id, mode)
        await self.coordinator.async_request_refresh()

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()


def _percentage_to_level(percentage: int) -> int:
    if percentage <= 0:
        return 0
    # Choose nearest manual level 1-6.
    best_level = 1
    best_diff = 101
    for level, pct in MANUAL_PERCENTAGES.items():
        diff = abs(pct - percentage)
        if diff < best_diff:
            best_diff = diff
            best_level = level
    return best_level
