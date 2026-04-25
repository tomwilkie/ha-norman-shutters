from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.norman_shutters.const import RETRY_DEADLINE
from custom_components.norman_shutters.coordinator import NormanCoordinator

SAMPLE_WINDOW = {
    "Id": 52280,
    "Name": "Right Window 1",
    "position": 37,
    "angle": 0,
    "battery": "57",
    "solar": 245,
    "Rssi": 67,
    "temp": 17,
}


# ---------------------------------------------------------------------------
# _parse_window_info
# ---------------------------------------------------------------------------


def test_parse_empty_windows():
    result = NormanCoordinator._parse_window_info({"totalWindow": 0, "windows": []})
    assert result == {}


def test_parse_missing_windows_key():
    result = NormanCoordinator._parse_window_info({})
    assert result == {}


def test_parse_id_stringified():
    result = NormanCoordinator._parse_window_info({"windows": [SAMPLE_WINDOW]})
    assert "52280" in result
    assert 52280 not in result


def test_parse_preserves_raw_dict():
    window = dict(SAMPLE_WINDOW)
    result = NormanCoordinator._parse_window_info({"windows": [window]})
    assert result["52280"] is window


def test_parse_multiple_windows():
    windows = [
        {**SAMPLE_WINDOW, "Id": 1, "Name": "Window A"},
        {**SAMPLE_WINDOW, "Id": 2, "Name": "Window B"},
    ]
    result = NormanCoordinator._parse_window_info({"windows": windows})
    assert set(result.keys()) == {"1", "2"}


# ---------------------------------------------------------------------------
# _async_update_data
# ---------------------------------------------------------------------------


async def test_update_data_success(fake_coordinator):
    """First attempt succeeds — no sleep, no re-login."""
    raw = {"windows": [dict(SAMPLE_WINDOW)]}
    fake_coordinator.client.get_window_info.return_value = raw
    fake_coordinator._async_setup = AsyncMock()

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await fake_coordinator._async_update_data()

    assert "52280" in result
    assert result["52280"]["Name"] == "Right Window 1"
    mock_sleep.assert_not_called()
    fake_coordinator._async_setup.assert_not_called()


async def test_update_data_retries_on_exception(fake_coordinator):
    """An exception on the first call triggers re-login + sleep, then success on retry."""
    raw_valid = {"windows": [dict(SAMPLE_WINDOW)]}
    call_count = 0

    def get_window_info():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OSError("session expired")
        return raw_valid

    fake_coordinator.client.get_window_info.side_effect = get_window_info
    fake_coordinator._async_setup = AsyncMock()

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await fake_coordinator._async_update_data()

    assert "52280" in result
    fake_coordinator._async_setup.assert_called_once()
    mock_sleep.assert_called_once_with(1.0)


async def test_update_data_retries_on_empty_list(fake_coordinator):
    """An empty-list response triggers re-login + sleep, then success on retry."""
    raw_empty = {"totalWindow": 0, "windows": []}
    raw_valid = {"windows": [dict(SAMPLE_WINDOW)]}
    call_count = 0

    def get_window_info():
        nonlocal call_count
        call_count += 1
        return raw_empty if call_count == 1 else raw_valid

    fake_coordinator.client.get_window_info.side_effect = get_window_info
    fake_coordinator._async_setup = AsyncMock()

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await fake_coordinator._async_update_data()

    assert "52280" in result
    fake_coordinator._async_setup.assert_called_once()
    mock_sleep.assert_called_once_with(1.0)


async def test_update_data_raises_after_deadline(fake_coordinator):
    """UpdateFailed is raised once cumulative sleep reaches RETRY_DEADLINE."""
    fake_coordinator.client.get_window_info.side_effect = OSError("always fails")
    fake_coordinator._async_setup = AsyncMock()

    # Each asyncio.sleep call advances elapsed by its argument; when elapsed
    # accumulates to RETRY_DEADLINE the next failure raises UpdateFailed.
    elapsed_tracker = [0.0]

    async def fake_sleep(seconds):
        elapsed_tracker[0] += seconds

    with (
        patch("asyncio.sleep", side_effect=fake_sleep),
        pytest.raises(Exception, match="Norman Hub unreachable after"),
    ):
        await fake_coordinator._async_update_data()

    assert elapsed_tracker[0] >= RETRY_DEADLINE


async def test_update_data_relogins_before_each_retry(fake_coordinator):
    """_async_setup is called before every retry, not just the first."""
    raw_valid = {"windows": [dict(SAMPLE_WINDOW)]}
    call_count = 0

    def get_window_info():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise OSError("not yet")
        return raw_valid

    fake_coordinator.client.get_window_info.side_effect = get_window_info
    fake_coordinator._async_setup = AsyncMock()

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await fake_coordinator._async_update_data()

    assert "52280" in result
    assert fake_coordinator._async_setup.call_count == 2


# ---------------------------------------------------------------------------
# async_request_aggressive_refresh — backoff scheduling
# ---------------------------------------------------------------------------


def _make_coordinator(fake_hass, scan_interval: int) -> NormanCoordinator:
    coordinator = NormanCoordinator(fake_hass, "192.168.1.100", scan_interval)
    coordinator.client = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


async def test_aggressive_refresh_calls_immediate_refresh(fake_hass):
    """Immediate async_request_refresh is always called."""
    coordinator = _make_coordinator(fake_hass, scan_interval=60)
    with patch(
        "custom_components.norman_shutters.coordinator.async_call_later",
        return_value=MagicMock(),
    ):
        await coordinator.async_request_aggressive_refresh()
    coordinator.async_request_refresh.assert_called_once()


async def test_aggressive_refresh_schedules_backoff_delays(fake_hass):
    """With scan_interval=60, backoff polls scheduled at cumulative delays 2, 6, 14, 30."""
    coordinator = _make_coordinator(fake_hass, scan_interval=60)
    with patch(
        "custom_components.norman_shutters.coordinator.async_call_later",
        return_value=MagicMock(),
    ) as mock_call_later:
        await coordinator.async_request_aggressive_refresh()

    delays = [c.args[1] for c in mock_call_later.call_args_list]
    assert delays == [2, 6, 14, 30]


async def test_aggressive_refresh_no_extra_polls_when_scan_interval_tiny(fake_hass):
    """With scan_interval=2, the initial backoff delay equals scan_interval — no polls scheduled."""
    coordinator = _make_coordinator(fake_hass, scan_interval=2)
    with patch(
        "custom_components.norman_shutters.coordinator.async_call_later",
        return_value=MagicMock(),
    ) as mock_call_later:
        await coordinator.async_request_aggressive_refresh()

    mock_call_later.assert_not_called()


async def test_aggressive_refresh_cancels_previous_sequence(fake_hass):
    """A second operation cancels all pending callbacks from the first."""
    coordinator = _make_coordinator(fake_hass, scan_interval=60)
    first_cancels = [MagicMock() for _ in range(4)]
    second_cancels = [MagicMock() for _ in range(4)]

    with patch(
        "custom_components.norman_shutters.coordinator.async_call_later",
        side_effect=first_cancels + second_cancels,
    ):
        await coordinator.async_request_aggressive_refresh()
        assert len(coordinator._aggressive_poll_unsubs) == 4

        await coordinator.async_request_aggressive_refresh()

    for cancel in first_cancels:
        cancel.assert_called_once()
    assert coordinator._aggressive_poll_unsubs == second_cancels


async def test_aggressive_refresh_immediate_refresh_called_each_time(fake_hass):
    """async_request_refresh is called once per aggressive refresh invocation."""
    coordinator = _make_coordinator(fake_hass, scan_interval=60)
    with patch(
        "custom_components.norman_shutters.coordinator.async_call_later",
        return_value=MagicMock(),
    ):
        await coordinator.async_request_aggressive_refresh()
        await coordinator.async_request_aggressive_refresh()

    assert coordinator.async_request_refresh.call_count == 2
