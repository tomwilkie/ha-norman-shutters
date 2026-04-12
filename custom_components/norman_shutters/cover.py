from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pynormanshutters import FULLY_OPEN_POSITION

from .const import DOMAIN
from .coordinator import NormanCoordinator
from .entity import NormanEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NormanCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(NormanCover(coordinator, window_id) for window_id in coordinator.data)


class NormanCover(NormanEntity, CoverEntity):
    """Cover entity representing a single Norman plantation shutter.

    These shutters are fixed panels — only the slats rotate. There is no
    vertical travel. OPEN/CLOSE fully open/close the slats; SET_TILT_POSITION
    sets a precise angle.
    """

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.SET_TILT_POSITION
    )

    def __init__(self, coordinator: NormanCoordinator, window_id: str) -> None:
        super().__init__(coordinator, window_id)
        self._attr_unique_id = window_id

    @property
    def name(self) -> str:
        return self._window.get("Name", self._window_id)

    @property
    def is_closed(self) -> bool | None:
        pos = self._window.get("position")
        if pos is None:
            return None
        return int(pos) == 0

    @property
    def current_cover_tilt_position(self) -> int | None:
        """Slat angle, normalised from 0-FULLY_OPEN_POSITION to 0-100."""
        raw = self._window.get("position")
        if raw is None:
            return None
        return round(int(raw) * 100 / FULLY_OPEN_POSITION)

    @property
    def _window_int_id(self) -> int:
        return int(self._window_id)

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.client.open_window, self._window_int_id
        )
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.coordinator.client.close_window, self._window_int_id
        )
        await self.coordinator.async_request_refresh()

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """HA sends 0-100; convert to hub's native 0-FULLY_OPEN_POSITION scale."""
        tilt_position: int = kwargs["tilt_position"]
        native = round(tilt_position * FULLY_OPEN_POSITION / 100)
        await self.hass.async_add_executor_job(
            self.coordinator.client.set_window_position, self._window_int_id, native
        )
        await self.coordinator.async_request_refresh()
