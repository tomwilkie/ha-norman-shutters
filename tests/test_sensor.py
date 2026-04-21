from custom_components.norman_shutters.sensor import (
    NormanBatterySensor,
    NormanRssiSensor,
    NormanTemperatureSensor,
)

BASE_WINDOW = {
    "Id": 42,
    "Name": "Bedroom",
    "position": 50,
    "battery": "75",
    "temp": 17,
    "Rssi": 67,
}


def make_sensor(coordinator, window_data):
    coordinator.data = {"42": window_data}
    return NormanBatterySensor(coordinator, "42")


def make_temperature_sensor(coordinator, window_data):
    coordinator.data = {"42": window_data}
    return NormanTemperatureSensor(coordinator, "42")


def make_rssi_sensor(coordinator, window_data):
    coordinator.data = {"42": window_data}
    return NormanRssiSensor(coordinator, "42")


# ---------------------------------------------------------------------------
# NormanBatterySensor — name
# ---------------------------------------------------------------------------


def test_name_with_Name_key(fake_coordinator):
    sensor = make_sensor(fake_coordinator, {**BASE_WINDOW, "Name": "Bedroom"})
    assert sensor.name == "Bedroom Battery"


def test_name_falls_back_to_window_id(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "Name"}
    sensor = make_sensor(fake_coordinator, data)
    assert sensor.name == "42 Battery"


# ---------------------------------------------------------------------------
# NormanBatterySensor — native_value
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
# NormanBatterySensor — unique_id
# ---------------------------------------------------------------------------


def test_unique_id(fake_coordinator):
    sensor = make_sensor(fake_coordinator, BASE_WINDOW)
    assert sensor._attr_unique_id == "42_battery"


# ---------------------------------------------------------------------------
# NormanTemperatureSensor — name
# ---------------------------------------------------------------------------


def test_temperature_name_with_Name_key(fake_coordinator):
    sensor = make_temperature_sensor(fake_coordinator, {**BASE_WINDOW, "Name": "Bedroom"})
    assert sensor.name == "Bedroom Temperature"


def test_temperature_name_falls_back_to_window_id(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "Name"}
    sensor = make_temperature_sensor(fake_coordinator, data)
    assert sensor.name == "42 Temperature"


# ---------------------------------------------------------------------------
# NormanTemperatureSensor — native_value
# ---------------------------------------------------------------------------


def test_temperature_native_value(fake_coordinator):
    sensor = make_temperature_sensor(fake_coordinator, {**BASE_WINDOW, "temp": 21})
    assert sensor.native_value == 21


def test_temperature_native_value_none_when_missing(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "temp"}
    sensor = make_temperature_sensor(fake_coordinator, data)
    assert sensor.native_value is None


# ---------------------------------------------------------------------------
# NormanTemperatureSensor — unique_id
# ---------------------------------------------------------------------------


def test_temperature_unique_id(fake_coordinator):
    sensor = make_temperature_sensor(fake_coordinator, BASE_WINDOW)
    assert sensor._attr_unique_id == "42_temperature"


# ---------------------------------------------------------------------------
# NormanRssiSensor — name
# ---------------------------------------------------------------------------


def test_rssi_name_with_Name_key(fake_coordinator):
    sensor = make_rssi_sensor(fake_coordinator, {**BASE_WINDOW, "Name": "Bedroom"})
    assert sensor.name == "Bedroom Signal Strength"


def test_rssi_name_falls_back_to_window_id(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "Name"}
    sensor = make_rssi_sensor(fake_coordinator, data)
    assert sensor.name == "42 Signal Strength"


# ---------------------------------------------------------------------------
# NormanRssiSensor — native_value
# ---------------------------------------------------------------------------


def test_rssi_native_value(fake_coordinator):
    sensor = make_rssi_sensor(fake_coordinator, {**BASE_WINDOW, "Rssi": 55})
    assert sensor.native_value == 55


def test_rssi_native_value_none_when_missing(fake_coordinator):
    data = {k: v for k, v in BASE_WINDOW.items() if k != "Rssi"}
    sensor = make_rssi_sensor(fake_coordinator, data)
    assert sensor.native_value is None


# ---------------------------------------------------------------------------
# NormanRssiSensor — unique_id
# ---------------------------------------------------------------------------


def test_rssi_unique_id(fake_coordinator):
    sensor = make_rssi_sensor(fake_coordinator, BASE_WINDOW)
    assert sensor._attr_unique_id == "42_rssi"
