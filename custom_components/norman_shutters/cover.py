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
from pynormanshutters import FULLY_CLOSED_POSITION

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
    """Cover entity representing a single Norman plantation shutter."""

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    def __init__(self, coordinator: NormanCoordinator, window_id: str) -> None:
        super().__init__(coordinator, window_id)
        self._attr_unique_id = window_id

    @property
    def name(self) -> str:
        return f"{self._window.get('Name', self._window_id)} Cover"

    @property
    def is_closed(self) -> bool | None:
        pos = self._window.get("position")
        if pos is None:
            return None
        return int(pos) >= FULLY_CLOSED_POSITION

    @property
    def _window_int_id(self) -> int:
        return int(self._window_id)

    async def async_open_cover(self, **kwargs: Any) -> None:
        _LOGGER.debug("open_cover called for window %s", self._window_id)
        await self.hass.async_add_executor_job(
            self.coordinator.client.open_window, self._window_int_id
        )
        await self.coordinator.async_request_aggressive_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        _LOGGER.debug("close_cover called for window %s", self._window_id)
        await self.hass.async_add_executor_job(
            self.coordinator.client.close_window, self._window_int_id
        )
        await self.coordinator.async_request_aggressive_refresh()
