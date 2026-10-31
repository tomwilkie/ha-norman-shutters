from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NormanCoordinator


def _format_mac(mac_hex: str) -> str:
    """Normalise a hex-only MAC string (AABBCCDDEEFF) to aa:bb:cc:dd:ee:ff."""
    mac = mac_hex.lower()
    return ":".join(mac[i : i + 2] for i in range(0, len(mac), 2))


def hub_device_kwargs(coordinator: NormanCoordinator) -> dict:
    """Device registry fields for the Norman Hub device."""
    hub_id = coordinator.mac_address or coordinator.host
    connections: set[tuple[str, str]] = set()
    if coordinator.mac_address:
        connections.add((CONNECTION_NETWORK_MAC, _format_mac(coordinator.mac_address)))
    return {
        "identifiers": {(DOMAIN, f"hub_{hub_id}")},
        "name": "Norman Hub",
        "manufacturer": "Norman",
        "model": "Norman Hub",
        "connections": connections,
    }


class NormanEntity(CoordinatorEntity[NormanCoordinator]):
    """Base entity for all Norman Shutters window devices."""

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
            via_device_id=self.coordinator.hub_device_id,
        )


class NormanHubEntity(CoordinatorEntity[NormanCoordinator]):
    """Base entity for Norman Hub-level devices."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NormanCoordinator) -> None:
        super().__init__(coordinator)

    @property
    def _hub_id(self) -> str:
        return self.coordinator.mac_address or self.coordinator.host

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(**hub_device_kwargs(self.coordinator))
