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
from .entity import NormanEntity, NormanHubEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NormanCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list = [NormanHubCover(coordinator)]
    entities.extend(NormanCover(coordinator, window_id) for window_id in coordinator.data)
    async_add_entities(entities)


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


class NormanHubCover(NormanHubEntity, CoverEntity):
    """Cover entity that opens or closes all Norman shutters on the hub at once."""

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    def __init__(self, coordinator: NormanCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "All Shutters"

    @property
    def unique_id(self) -> str:
        return f"hub_{self._hub_id}_cover"

    @property
    def is_closed(self) -> bool | None:
        if not self.coordinator.data:
            return None
        positions = [w.get("position") for w in self.coordinator.data.values()]
        if any(p is None for p in positions):
            return None
        return all(int(p) >= FULLY_CLOSED_POSITION for p in positions)

    async def async_open_cover(self, **kwargs: Any) -> None:
        _LOGGER.debug("open_cover called for all windows")
        await self.hass.async_add_executor_job(self.coordinator.client.full_open)
        await self.coordinator.async_request_aggressive_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        _LOGGER.debug("close_cover called for all windows")
        await self.hass.async_add_executor_job(self.coordinator.client.full_close)
        await self.coordinator.async_request_aggressive_refresh()
