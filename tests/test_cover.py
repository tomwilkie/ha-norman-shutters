import pynormanshutters

from custom_components.norman_shutters.cover import NormanCover

FULLY_OPEN_POSITION = pynormanshutters.FULLY_OPEN_POSITION  # 37 — slats open
FULLY_CLOSED_POSITION = pynormanshutters.FULLY_CLOSED_POSITION  # 100 — slats closed

BASE_WINDOW = {
    "Id": 42,
    "Name": "Living Room",
    "position": FULLY_OPEN_POSITION,
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
    assert cover.name == "Lounge Cover"


def test_name_falls_back_to_window_id(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "Name"}
    cover = make_cover(fake_coordinator, data)
    assert cover.name == "42 Cover"


# ---------------------------------------------------------------------------
# is_closed
# ---------------------------------------------------------------------------


def test_is_closed_at_fully_closed(fake_coordinator):
    cover = make_cover(fake_coordinator, {**BASE_WINDOW, "position": FULLY_CLOSED_POSITION})
    assert cover.is_closed is True


def test_is_closed_false_when_open(fake_coordinator):
    cover = make_cover(fake_coordinator, {**BASE_WINDOW, "position": FULLY_OPEN_POSITION})
    assert cover.is_closed is False


def test_is_closed_false_at_midpoint(fake_coordinator):
    mid = (FULLY_OPEN_POSITION + FULLY_CLOSED_POSITION) // 2
    cover = make_cover(fake_coordinator, {**BASE_WINDOW, "position": mid})
    assert cover.is_closed is False


def test_is_closed_none_when_missing(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "position"}
    cover = make_cover(fake_coordinator, data)
    assert cover.is_closed is None


# ---------------------------------------------------------------------------
# available
# ---------------------------------------------------------------------------


def test_available_when_window_id_present(fake_coordinator):
    cover = make_cover(fake_coordinator, BASE_WINDOW)
    assert cover.available is True


def test_unavailable_when_window_id_missing(fake_coordinator):
    cover = make_cover(fake_coordinator, BASE_WINDOW)
    fake_coordinator.data = {}  # window disappears from coordinator
    assert cover.available is False


def test_is_closed_none_when_unavailable(fake_coordinator):
    cover = make_cover(fake_coordinator, BASE_WINDOW)
    fake_coordinator.data = {}
    assert cover.is_closed is None


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
    fake_coordinator.async_request_aggressive_refresh.assert_called_once()


async def test_close_cover(fake_coordinator):
    cover = make_cover(fake_coordinator, BASE_WINDOW)
    await cover.async_close_cover()
    fake_coordinator.client.close_window.assert_called_once_with(42)
    fake_coordinator.async_request_aggressive_refresh.assert_called_once()
