from unittest.mock import AsyncMock

import pytest

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
    raw = {"windows": [dict(SAMPLE_WINDOW)]}
    fake_coordinator.client.get_window_info.return_value = raw

    result = await fake_coordinator._async_update_data()

    assert "52280" in result
    assert result["52280"]["Name"] == "Right Window 1"


async def test_update_data_retries_on_failure(fake_coordinator):
    raw = {"windows": [dict(SAMPLE_WINDOW)]}
    call_count = 0

    def get_window_info():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise OSError("session expired")
        return raw

    fake_coordinator.client.get_window_info.side_effect = get_window_info
    fake_coordinator._async_setup = AsyncMock()

    result = await fake_coordinator._async_update_data()

    fake_coordinator._async_setup.assert_called_once()
    assert "52280" in result


async def test_update_data_raises_update_failed(fake_coordinator):
    fake_coordinator.client.get_window_info.side_effect = OSError("always fails")
    fake_coordinator._async_setup = AsyncMock()

    with pytest.raises(Exception, match="Error communicating"):
        await fake_coordinator._async_update_data()
