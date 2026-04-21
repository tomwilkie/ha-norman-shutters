from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NormanCoordinator


class NormanEntity(CoordinatorEntity[NormanCoordinator]):
    """Base entity for all Norman Shutters devices."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NormanCoordinator, window_id: str) -> None:
        super().__init__(coordinator)
        self._window_id = window_id

    @property
    def available(self) -> bool:
        return self._window_id in self.coordinator.data

    @property
    def _window(self) -> dict:
        return self.coordinator.data.get(self._window_id, {})

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._window_id)},
            name=self._window.get("Name", self._window_id),
            manufacturer="Norman",
            model="PerfectTilt",
        )
