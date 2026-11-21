from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.components.cover import CoverState
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_CLOSE_COVER, SERVICE_OPEN_COVER
from homeassistant.core import HomeAssistant
from pytest_homeassistant.common import MockConfigEntry

from custom_components.norman_shutters.const import DOMAIN

from .conftest import MAC, WINDOW_A, WINDOW_B, entity_id_for

HUB_COVER_UID = f"hub_{MAC}_cover"


async def _refresh(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    await hass.data[DOMAIN][entry.entry_id].async_refresh()
    await hass.async_block_till_done()


@pytest.fixture(autouse=True)
def no_backoff_timers():
    """Don't schedule the follow-up polls after a command."""
    with patch(
        "custom_components.norman_shutters.coordinator.async_call_later",
        return_value=MagicMock(),
    ):
        yield


async def test_window_cover_states(hass: HomeAssistant, init_integration: MockConfigEntry) -> None:
    open_window = hass.states.get(entity_id_for(hass, COVER_DOMAIN, str(WINDOW_A["Id"])))
    closed_window = hass.states.get(entity_id_for(hass, COVER_DOMAIN, str(WINDOW_B["Id"])))

    assert open_window.state == CoverState.OPEN
    assert open_window.attributes["friendly_name"] == "Right Window 1"
    assert open_window.attributes["device_class"] == "shutter"
    assert closed_window.state == CoverState.CLOSED


async def test_hub_cover_open_when_any_window_open(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    state = hass.states.get(entity_id_for(hass, COVER_DOMAIN, HUB_COVER_UID))

    assert state.state == CoverState.OPEN
    assert state.attributes["friendly_name"] == "Norman Hub All Shutters"


async def test_hub_cover_closed_when_all_closed(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    mock_client.get_window_info.return_value = {
        "windows": [{**WINDOW_A, "position": 100}, dict(WINDOW_B)]
    }
    await _refresh(hass, init_integration)

    assert hass.states.get(entity_id_for(hass, COVER_DOMAIN, HUB_COVER_UID)).state == (
        CoverState.CLOSED
    )


async def test_cover_unknown_when_position_missing(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    window = {k: v for k, v in WINDOW_A.items() if k != "position"}
    mock_client.get_window_info.return_value = {"windows": [window, dict(WINDOW_B)]}
    await _refresh(hass, init_integration)

    assert hass.states.get(entity_id_for(hass, COVER_DOMAIN, str(WINDOW_A["Id"]))).state == (
        "unknown"
    )
    assert hass.states.get(entity_id_for(hass, COVER_DOMAIN, HUB_COVER_UID)).state == "unknown"


async def test_cover_unavailable_when_window_disappears(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    mock_client.get_window_info.return_value = {"windows": [dict(WINDOW_B)]}
    await _refresh(hass, init_integration)

    assert hass.states.get(entity_id_for(hass, COVER_DOMAIN, str(WINDOW_A["Id"]))).state == (
        "unavailable"
    )


@pytest.mark.parametrize(
    ("service", "method"),
    [(SERVICE_OPEN_COVER, "open_window"), (SERVICE_CLOSE_COVER, "close_window")],
)
async def test_window_cover_commands(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    service: str,
    method: str,
) -> None:
    polls_before = mock_client.get_window_info.call_count
    await hass.services.async_call(
        COVER_DOMAIN,
        service,
        {ATTR_ENTITY_ID: entity_id_for(hass, COVER_DOMAIN, str(WINDOW_A["Id"]))},
        blocking=True,
    )
    await hass.async_block_till_done()

    getattr(mock_client, method).assert_called_once_with(WINDOW_A["Id"])
    assert mock_client.get_window_info.call_count > polls_before


@pytest.mark.parametrize(
    ("service", "method"),
    [(SERVICE_OPEN_COVER, "fullopen"), (SERVICE_CLOSE_COVER, "fullclose")],
)
async def test_hub_cover_commands(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    service: str,
    method: str,
) -> None:
    await hass.services.async_call(
        COVER_DOMAIN,
        service,
        {ATTR_ENTITY_ID: entity_id_for(hass, COVER_DOMAIN, HUB_COVER_UID)},
        blocking=True,
    )

    getattr(mock_client, method).assert_called_once_with()
