"""Shared fixtures. Tests run against a real Home Assistant via pytest-homeassistant."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.norman_shutters.const import CONF_HOST, CONF_MAC, DOMAIN

HOST = "192.168.1.100"
MAC = "AABBCCDDEEFF"

WINDOW_A = {
    "Id": 52280,
    "Name": "Right Window 1",
    "position": 37,
    "angle": 0,
    "battery": "57",
    "solar": 245,
    "Rssi": 67,
    "temp": 17,
}
WINDOW_B = {**WINDOW_A, "Id": 52281, "Name": "Left Window 1", "position": 100}


@pytest.fixture
def mock_client() -> MagicMock:
    """A pynormanshutters client returning two windows."""
    client = MagicMock()
    client.get_window_info.return_value = {
        "totalWindow": 2,
        "windows": [dict(WINDOW_A), dict(WINDOW_B)],
    }
    return client


@pytest.fixture
def mock_login(mock_client: MagicMock) -> Generator[MagicMock]:
    """Patch login() everywhere the integration imports it."""
    with (
        patch(
            "custom_components.norman_shutters.coordinator.login", return_value=mock_client
        ) as login,
        patch("custom_components.norman_shutters.config_flow.login", new=login),
    ):
        yield login


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"Norman Hub ({HOST})",
        data={CONF_HOST: HOST, CONF_MAC: MAC},
        unique_id=MAC,
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_login: MagicMock
) -> MockConfigEntry:
    """Set up the integration with a mocked hub."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


def entity_id_for(hass: HomeAssistant, platform: str, unique_id: str) -> str:
    """Look up an entity_id by its unique_id."""
    entity_id = er.async_get(hass).async_get_entity_id(platform, DOMAIN, unique_id)
    assert entity_id is not None, f"no {platform} entity with unique_id {unique_id}"
    return entity_id
