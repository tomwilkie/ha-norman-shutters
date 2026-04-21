from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfSignalStrength, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import NormanCoordinator
from .entity import NormanEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: NormanCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        entity
        for window_id in coordinator.data
        for entity in [
            NormanBatterySensor(coordinator, window_id),
            NormanTemperatureSensor(coordinator, window_id),
            NormanRssiSensor(coordinator, window_id),
        ]
    )


class NormanBatterySensor(NormanEntity, SensorEntity):
    """Battery level sensor for a Norman Shutter window."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: NormanCoordinator, window_id: str) -> None:
        super().__init__(coordinator, window_id)
        self._attr_unique_id = f"{window_id}_battery"

    @property
    def name(self) -> str:
        return f"{self._window.get('Name', self._window_id)} Battery"

    @property
    def native_value(self) -> int | None:
        val = self._window.get("battery")
        return int(val) if val is not None else None


class NormanTemperatureSensor(NormanEntity, SensorEntity):
    """Temperature sensor for a Norman Shutter window."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: NormanCoordinator, window_id: str) -> None:
        super().__init__(coordinator, window_id)
        self._attr_unique_id = f"{window_id}_temperature"

    @property
    def name(self) -> str:
        return f"{self._window.get('Name', self._window_id)} Temperature"

    @property
    def native_value(self) -> int | None:
        val = self._window.get("temp")
        return int(val) if val is not None else None


class NormanRssiSensor(NormanEntity, SensorEntity):
    """Signal strength (RSSI) sensor for a Norman Shutter window."""

    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = UnitOfSignalStrength.DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: NormanCoordinator, window_id: str) -> None:
        super().__init__(coordinator, window_id)
        self._attr_unique_id = f"{window_id}_rssi"

    @property
    def name(self) -> str:
        return f"{self._window.get('Name', self._window_id)} Signal Strength"

    @property
    def native_value(self) -> int | None:
        val = self._window.get("Rssi")
        return int(val) if val is not None else None
