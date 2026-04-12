import pynormanshutters

from custom_components.norman_shutters.cover import NormanCover

FULLY_OPEN_POSITION = pynormanshutters.FULLY_OPEN_POSITION

BASE_WINDOW = {
    "Id": 42,
    "Name": "Living Room",
    "position": 50,
    "angle": 0,
    "battery": "75",
    "solar": 200,
    "Rssi": 60,
    "temp": 20,
}


def make_cover(coordinator, window_data):
    coordinator.data = {"42": window_data}
    return NormanCover(coordinator, "42")


# ---------------------------------------------------------------------------
# name
# ---------------------------------------------------------------------------


def test_name_from_Name_key(fake_coordinator):
    cover = make_cover(fake_coordinator, {**BASE_WINDOW, "Name": "Lounge"})
    assert cover.name == "Lounge"


def test_name_falls_back_to_window_id(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "Name"}
    cover = make_cover(fake_coordinator, data)
    assert cover.name == "42"


# ---------------------------------------------------------------------------
# is_closed
# ---------------------------------------------------------------------------


def test_is_closed_zero(fake_coordinator):
    cover = make_cover(fake_coordinator, {**BASE_WINDOW, "position": 0})
    assert cover.is_closed is True


def test_is_closed_nonzero(fake_coordinator):
    cover = make_cover(fake_coordinator, {**BASE_WINDOW, "position": 50})
    assert cover.is_closed is False


def test_is_closed_string_zero(fake_coordinator):
    cover = make_cover(fake_coordinator, {**BASE_WINDOW, "position": "0"})
    assert cover.is_closed is True


def test_is_closed_none_when_missing(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "position"}
    cover = make_cover(fake_coordinator, data)
    assert cover.is_closed is None


# ---------------------------------------------------------------------------
# current_cover_tilt_position
# ---------------------------------------------------------------------------


def test_tilt_fully_open(fake_coordinator):
    cover = make_cover(fake_coordinator, {**BASE_WINDOW, "position": FULLY_OPEN_POSITION})
    assert cover.current_cover_tilt_position == 100


def test_tilt_half(fake_coordinator):
    cover = make_cover(fake_coordinator, {**BASE_WINDOW, "position": FULLY_OPEN_POSITION // 2})
    assert cover.current_cover_tilt_position == 50


def test_tilt_zero(fake_coordinator):
    cover = make_cover(fake_coordinator, {**BASE_WINDOW, "position": 0})
    assert cover.current_cover_tilt_position == 0


def test_tilt_none_when_missing(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "position"}
    cover = make_cover(fake_coordinator, data)
    assert cover.current_cover_tilt_position is None


# ---------------------------------------------------------------------------
# _window_int_id
# ---------------------------------------------------------------------------


def test_window_int_id(fake_coordinator):
    cover = make_cover(fake_coordinator, BASE_WINDOW)
    assert cover._window_int_id == 42


# ---------------------------------------------------------------------------
# async actions
# ---------------------------------------------------------------------------


async def test_open_cover(fake_coordinator):
    cover = make_cover(fake_coordinator, BASE_WINDOW)
    await cover.async_open_cover()
    fake_coordinator.client.open_window.assert_called_once_with(42)
    fake_coordinator.async_request_refresh.assert_called_once()


async def test_close_cover(fake_coordinator):
    cover = make_cover(fake_coordinator, BASE_WINDOW)
    await cover.async_close_cover()
    fake_coordinator.client.close_window.assert_called_once_with(42)
    fake_coordinator.async_request_refresh.assert_called_once()


async def test_set_tilt_position_math(fake_coordinator):
    cover = make_cover(fake_coordinator, BASE_WINDOW)
    tilt_pct = 50
    expected_native = round(tilt_pct * FULLY_OPEN_POSITION / 100)

    await cover.async_set_cover_tilt_position(tilt_position=tilt_pct)

    fake_coordinator.client.set_window_position.assert_called_once_with(42, expected_native)
    fake_coordinator.async_request_refresh.assert_called_once()
