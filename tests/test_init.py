from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import custom_components.norman_shutters as integration


async def test_setup_registers_hub_and_stores_device_id(fake_hass):
    entry = MagicMock()
    entry.entry_id = "entry-1"
    entry.data = {"host": "192.168.1.100", "mac_address": "AABBCCDDEEFF"}
    entry.options = {}
    fake_hass.data = {}
    fake_hass.config_entries.async_forward_entry_setups = AsyncMock()

    registry = MagicMock()
    registry.async_get_or_create.return_value = SimpleNamespace(id="hub-device-id")

    with (
        patch.object(integration.NormanCoordinator, "_async_setup", AsyncMock()),
        patch.object(
            integration.NormanCoordinator,
            "async_config_entry_first_refresh",
            AsyncMock(),
            create=True,
        ),
        patch.object(integration.dr, "async_get", return_value=registry),
    ):
        assert await integration.async_setup_entry(fake_hass, entry)

    kwargs = registry.async_get_or_create.call_args.kwargs
    assert kwargs["config_entry_id"] == "entry-1"
    assert kwargs["identifiers"] == {("norman_shutters", "hub_AABBCCDDEEFF")}
    assert ("mac", "aa:bb:cc:dd:ee:ff") in kwargs["connections"]
    coordinator = fake_hass.data["norman_shutters"]["entry-1"]
    assert coordinator.hub_device_id == "hub-device-id"
    fake_hass.config_entries.async_forward_entry_setups.assert_awaited_once()
