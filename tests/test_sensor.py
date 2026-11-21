from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.core import HomeAssistant
from pytest_homeassistant.common import MockConfigEntry

from custom_components.norman_shutters.const import DOMAIN

from .conftest import MAC, WINDOW_A, WINDOW_B, entity_id_for

WINDOW_ID = str(WINDOW_A["Id"])


@pytest.mark.parametrize(
    ("suffix", "name", "value", "unit", "device_class"),
    [
        ("battery", "Right Window 1 Battery", "57", "%", "battery"),
        ("temperature", "Right Window 1 Temperature", "17", "°C", "temperature"),
        ("rssi", "Right Window 1 Signal Strength", "67", "dBm", "signal_strength"),
    ],
)
async def test_window_sensors(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    suffix: str,
    name: str,
    value: str,
    unit: str,
    device_class: str,
) -> None:
    state = hass.states.get(entity_id_for(hass, SENSOR_DOMAIN, f"{WINDOW_ID}_{suffix}"))

    assert state.state == value
    assert state.attributes["friendly_name"] == name
    assert state.attributes["unit_of_measurement"] == unit
    assert state.attributes["device_class"] == device_class
    assert state.attributes["state_class"] == "measurement"


async def test_connected_shutters_sensor(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    state = hass.states.get(entity_id_for(hass, SENSOR_DOMAIN, f"hub_{MAC}_connected_shutters"))

    assert state.state == "2"
    assert state.attributes["friendly_name"] == "Norman Hub Connected Shutters"


async def test_sensors_unknown_when_fields_missing(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    window = {k: v for k, v in WINDOW_A.items() if k not in ("battery", "temp", "Rssi")}
    mock_client.get_window_info.return_value = {"windows": [window, dict(WINDOW_B)]}
    await hass.data[DOMAIN][init_integration.entry_id].async_refresh()
    await hass.async_block_till_done()

    for suffix in ("battery", "temperature", "rssi"):
        entity_id = entity_id_for(hass, SENSOR_DOMAIN, f"{WINDOW_ID}_{suffix}")
        assert hass.states.get(entity_id).state == "unknown"


async def test_battery_accepts_int(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    mock_client.get_window_info.return_value = {"windows": [{**WINDOW_A, "battery": 80}]}
    await hass.data[DOMAIN][init_integration.entry_id].async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(entity_id_for(hass, SENSOR_DOMAIN, f"{WINDOW_ID}_battery")).state == (
        "80"
    )
