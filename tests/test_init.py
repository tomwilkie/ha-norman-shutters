from unittest.mock import MagicMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant.common import MockConfigEntry

from custom_components.norman_shutters.const import DOMAIN

from .conftest import MAC, WINDOW_A


async def test_setup_and_unload(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    assert init_integration.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    assert init_integration.state is ConfigEntryState.NOT_LOADED
    assert init_integration.entry_id not in hass.data[DOMAIN]


async def test_setup_retries_when_login_fails(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_login: MagicMock
) -> None:
    mock_login.side_effect = OSError("no route to host")
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_hub_device_registered(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    registry = dr.async_get(hass)
    hub = registry.async_get_device_by_identifier((DOMAIN, f"hub_{MAC}"), init_integration.entry_id)

    assert hub is not None
    assert hub.name == "Norman Hub"
    assert hub.manufacturer == "Norman"
    assert (dr.CONNECTION_NETWORK_MAC, "aa:bb:cc:dd:ee:ff") in hub.connections
    assert hass.data[DOMAIN][init_integration.entry_id].hub_device_id == hub.id


async def test_window_devices_link_to_hub(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    registry = dr.async_get(hass)
    entry_id = init_integration.entry_id
    hub = registry.async_get_device_by_identifier((DOMAIN, f"hub_{MAC}"), entry_id)
    window = registry.async_get_device_by_identifier((DOMAIN, str(WINDOW_A["Id"])), entry_id)

    assert window is not None
    assert window.name == "Right Window 1"
    assert window.model == "PerfectTilt"
    assert window.via_device_id == hub.id


async def test_options_update_reloads_entry(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_login: MagicMock
) -> None:
    logins_before = mock_login.call_count

    hass.config_entries.async_update_entry(init_integration, options={"scan_interval": 120})
    await hass.async_block_till_done()

    assert init_integration.state is ConfigEntryState.LOADED
    assert mock_login.call_count > logins_before
