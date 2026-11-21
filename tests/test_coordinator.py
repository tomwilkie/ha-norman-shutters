from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.norman_shutters.const import RETRY_DEADLINE
from custom_components.norman_shutters.coordinator import NormanCoordinator

from .conftest import HOST, WINDOW_A

# ---------------------------------------------------------------------------
# _parse_window_info
# ---------------------------------------------------------------------------


def test_parse_empty_windows():
    assert NormanCoordinator._parse_window_info({"totalWindow": 0, "windows": []}) == {}


def test_parse_missing_windows_key():
    assert NormanCoordinator._parse_window_info({}) == {}


def test_parse_id_stringified():
    result = NormanCoordinator._parse_window_info({"windows": [WINDOW_A]})
    assert "52280" in result
    assert 52280 not in result


def test_parse_preserves_raw_dict():
    window = dict(WINDOW_A)
    assert NormanCoordinator._parse_window_info({"windows": [window]})["52280"] is window


def test_parse_multiple_windows():
    windows = [{**WINDOW_A, "Id": 1}, {**WINDOW_A, "Id": 2}]
    assert set(NormanCoordinator._parse_window_info({"windows": windows})) == {"1", "2"}


# ---------------------------------------------------------------------------
# _async_update_data
# ---------------------------------------------------------------------------


@pytest.fixture
def coordinator(hass: HomeAssistant) -> NormanCoordinator:
    coordinator = NormanCoordinator(hass, HOST)
    coordinator.client = MagicMock()
    coordinator._async_setup = AsyncMock()
    return coordinator


async def test_update_data_success(coordinator: NormanCoordinator) -> None:
    """First attempt succeeds — no sleep, no re-login."""
    coordinator.client.get_window_info.return_value = {"windows": [dict(WINDOW_A)]}

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await coordinator._async_update_data()

    assert result["52280"]["Name"] == "Right Window 1"
    mock_sleep.assert_not_called()
    coordinator._async_setup.assert_not_called()


@pytest.mark.parametrize(
    "first_response",
    [OSError("session expired"), {"totalWindow": 0, "windows": []}],
    ids=["exception", "empty_list"],
)
async def test_update_data_retries_once(coordinator: NormanCoordinator, first_response) -> None:
    """A failure or empty list triggers re-login + sleep, then success on retry."""
    coordinator.client.get_window_info.side_effect = [
        first_response,
        {"windows": [dict(WINDOW_A)]},
    ]

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await coordinator._async_update_data()

    assert "52280" in result
    coordinator._async_setup.assert_called_once()
    mock_sleep.assert_called_once_with(1.0)


async def test_update_data_relogins_before_each_retry(coordinator: NormanCoordinator) -> None:
    coordinator.client.get_window_info.side_effect = [
        OSError("not yet"),
        OSError("not yet"),
        {"windows": [dict(WINDOW_A)]},
    ]

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await coordinator._async_update_data()

    assert coordinator._async_setup.call_count == 2


async def test_update_data_raises_after_deadline(coordinator: NormanCoordinator) -> None:
    """UpdateFailed (or its Unreachable subclass) once cumulative sleep hits RETRY_DEADLINE."""
    coordinator.client.get_window_info.side_effect = OSError("always fails")
    slept = [0.0]

    async def fake_sleep(seconds):
        slept[0] += seconds

    with (
        patch("asyncio.sleep", side_effect=fake_sleep),
        pytest.raises(UpdateFailed, match="Norman Hub unreachable after"),
    ):
        await coordinator._async_update_data()

    assert slept[0] >= RETRY_DEADLINE


# ---------------------------------------------------------------------------
# async_request_aggressive_refresh — backoff scheduling
# ---------------------------------------------------------------------------


def _make_coordinator(hass: HomeAssistant, scan_interval: int) -> NormanCoordinator:
    coordinator = NormanCoordinator(hass, HOST, scan_interval)
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


@pytest.mark.parametrize(
    ("scan_interval", "expected"),
    [(60, [2, 6, 14, 30]), (2, [])],
)
async def test_aggressive_refresh_schedule(
    hass: HomeAssistant, scan_interval: int, expected: list[int]
) -> None:
    coordinator = _make_coordinator(hass, scan_interval)
    with patch(
        "custom_components.norman_shutters.coordinator.async_call_later",
        return_value=MagicMock(),
    ) as mock_call_later:
        await coordinator.async_request_aggressive_refresh()

    coordinator.async_request_refresh.assert_called_once()
    assert [c.args[1] for c in mock_call_later.call_args_list] == expected


async def test_aggressive_refresh_cancels_previous_sequence(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, 60)
    first = [MagicMock() for _ in range(4)]
    second = [MagicMock() for _ in range(4)]

    with patch(
        "custom_components.norman_shutters.coordinator.async_call_later",
        side_effect=first + second,
    ):
        await coordinator.async_request_aggressive_refresh()
        await coordinator.async_request_aggressive_refresh()

    for cancel in first:
        cancel.assert_called_once()
    assert coordinator._aggressive_poll_unsubs == second
    assert coordinator.async_request_refresh.call_count == 2


async def test_shutdown_cancels_backoff_polls(hass: HomeAssistant) -> None:
    coordinator = _make_coordinator(hass, 60)
    cancels = [MagicMock() for _ in range(4)]

    with patch(
        "custom_components.norman_shutters.coordinator.async_call_later",
        side_effect=cancels,
    ):
        await coordinator.async_request_aggressive_refresh()
    await coordinator.async_shutdown()

    for cancel in cancels:
        cancel.assert_called_once()
    assert coordinator._aggressive_poll_unsubs == []
