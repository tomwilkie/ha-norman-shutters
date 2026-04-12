from custom_components.norman_shutters.sensor import NormanBatterySensor

BASE_WINDOW = {
    "Id": 42,
    "Name": "Bedroom",
    "position": 50,
    "battery": "75",
}


def make_sensor(coordinator, window_data):
    coordinator.data = {"42": window_data}
    return NormanBatterySensor(coordinator, "42")


# ---------------------------------------------------------------------------
# name
# ---------------------------------------------------------------------------


def test_name_with_Name_key(fake_coordinator):
    sensor = make_sensor(fake_coordinator, {**BASE_WINDOW, "Name": "Bedroom"})
    assert sensor.name == "Bedroom Battery"


def test_name_falls_back_to_window_id(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "Name"}
    sensor = make_sensor(fake_coordinator, data)
    assert sensor.name == "42 Battery"


# ---------------------------------------------------------------------------
# native_value
# ---------------------------------------------------------------------------


def test_native_value_string(fake_coordinator):
    sensor = make_sensor(fake_coordinator, {**BASE_WINDOW, "battery": "57"})
    assert sensor.native_value == 57


def test_native_value_int(fake_coordinator):
    sensor = make_sensor(fake_coordinator, {**BASE_WINDOW, "battery": 80})
    assert sensor.native_value == 80


def test_native_value_none_when_missing(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "battery"}
    sensor = make_sensor(fake_coordinator, data)
    assert sensor.native_value is None


# ---------------------------------------------------------------------------
# unique_id
# ---------------------------------------------------------------------------


def test_unique_id(fake_coordinator):
    sensor = make_sensor(fake_coordinator, BASE_WINDOW)
    assert sensor._attr_unique_id == "42_battery"
