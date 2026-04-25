"""
Stub all Home Assistant and pynormanshutters imports at module scope so that
integration modules can be imported without installing homeassistant or
pynormanshutters.  This file is loaded by pytest before any test module, so
the sys.modules patch is in place when test files import from
custom_components.
"""

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Stub base classes — must be real Python classes, not MagicMock, because
# the integration classes inherit from them.
# ---------------------------------------------------------------------------


class FakeDataUpdateCoordinator:
    def __init__(self, hass, logger, *, name, update_interval, config_entry=None):
        self.hass = hass
        self.data = {}
        self.last_update_success = True


class FakeCoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.hass = coordinator.hass

    def __class_getitem__(cls, item):
        # Support CoordinatorEntity[NormanCoordinator] generic syntax in entity.py
        return cls


class FakeOptionsFlow:
    """Minimal OptionsFlow stub."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    def async_show_form(
        self, *, step_id, data_schema=None, errors=None, description_placeholders=None
    ):
        return {"type": "form", "step_id": step_id, "errors": errors or {}}

    def async_create_entry(self, *, title, data):
        return {"type": "create_entry", "title": title, "data": data}


class FakeConfigFlow:
    """Minimal ConfigFlow stub that handles the 'domain=' class keyword."""

    VERSION = 1

    def __init_subclass__(cls, domain=None, **kwargs):
        super().__init_subclass__(**kwargs)

    async def async_set_unique_id(self, uid):
        pass

    def _abort_if_unique_id_configured(self, updates=None):
        pass

    def async_show_form(
        self,
        *,
        step_id,
        data_schema=None,
        errors=None,
        description_placeholders=None,
    ):
        return {"type": "form", "step_id": step_id, "errors": errors or {}}

    def async_create_entry(self, *, title, data):
        return {"type": "create_entry", "title": title, "data": data}


# CoverEntityFeature constants must be integers for bitwise OR at class
# definition time (NormanCover sets _attr_supported_features = OPEN | CLOSE | ...).
_CoverEntityFeature = SimpleNamespace(OPEN=1, CLOSE=2, SET_TILT_POSITION=4)
_CoverDeviceClass = SimpleNamespace(SHUTTER="shutter")
_SensorDeviceClass = SimpleNamespace(
    BATTERY="battery",
    TEMPERATURE="temperature",
    SIGNAL_STRENGTH="signal_strength",
)
_SensorStateClass = SimpleNamespace(MEASUREMENT="measurement")


# ---------------------------------------------------------------------------
# Build and inject fake HA module tree
# ---------------------------------------------------------------------------


def _mod(name, **attrs):
    m = ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


_login_mock = MagicMock()

sys.modules.update(
    {
        "homeassistant": _mod("homeassistant"),
        "homeassistant.core": _mod(
            "homeassistant.core",
            HomeAssistant=MagicMock,
            callback=lambda fn: fn,
        ),
        "homeassistant.config_entries": _mod(
            "homeassistant.config_entries",
            ConfigEntry=MagicMock,
            ConfigFlow=FakeConfigFlow,
            OptionsFlow=FakeOptionsFlow,
        ),
        "homeassistant.data_entry_flow": _mod(
            "homeassistant.data_entry_flow",
            FlowResult=dict,
        ),
        "homeassistant.components": _mod("homeassistant.components"),
        "homeassistant.components.cover": _mod(
            "homeassistant.components.cover",
            CoverEntity=object,
            CoverEntityFeature=_CoverEntityFeature,
            CoverDeviceClass=_CoverDeviceClass,
        ),
        "homeassistant.components.sensor": _mod(
            "homeassistant.components.sensor",
            SensorEntity=object,
            SensorDeviceClass=_SensorDeviceClass,
            SensorStateClass=_SensorStateClass,
        ),
        "homeassistant.components.zeroconf": _mod("homeassistant.components.zeroconf"),
        "homeassistant.const": _mod(
            "homeassistant.const",
            PERCENTAGE="%",
            UnitOfTemperature=SimpleNamespace(CELSIUS="°C"),
            UnitOfSignalStrength=SimpleNamespace(DECIBELS_MILLIWATT="dBm"),
        ),
        "homeassistant.helpers": _mod("homeassistant.helpers"),
        "homeassistant.helpers.service_info": _mod("homeassistant.helpers.service_info"),
        "homeassistant.helpers.service_info.zeroconf": _mod(
            "homeassistant.helpers.service_info.zeroconf",
            ZeroconfServiceInfo=MagicMock,
        ),
        "homeassistant.helpers.update_coordinator": _mod(
            "homeassistant.helpers.update_coordinator",
            DataUpdateCoordinator=FakeDataUpdateCoordinator,
            CoordinatorEntity=FakeCoordinatorEntity,
            UpdateFailed=Exception,
        ),
        "homeassistant.helpers.device_registry": _mod(
            "homeassistant.helpers.device_registry",
            DeviceInfo=dict,
            CONNECTION_NETWORK_MAC="mac",
        ),
        "homeassistant.helpers.entity_platform": _mod(
            "homeassistant.helpers.entity_platform",
            AddEntitiesCallback=None,
        ),
        "homeassistant.helpers.event": _mod(
            "homeassistant.helpers.event",
            async_call_later=MagicMock(return_value=MagicMock()),
        ),
        "homeassistant.exceptions": _mod(
            "homeassistant.exceptions",
            ConfigEntryNotReady=Exception,
        ),
        "pynormanshutters": _mod(
            "pynormanshutters",
            login=_login_mock,
            FULLY_OPEN_POSITION=37,
            FULLY_CLOSED_POSITION=100,
        ),
        "voluptuous": _mod(
            "voluptuous",
            Schema=MagicMock(),
            Required=MagicMock(),
            Optional=MagicMock(),
            All=MagicMock(),
            Range=MagicMock(),
        ),
    }
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_hass():
    """Minimal hass-like object with a synchronous async_add_executor_job."""
    hass = MagicMock()
    hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *args: fn(*args))
    return hass


@pytest.fixture
def fake_coordinator(fake_hass):
    """NormanCoordinator wired to fake_hass with a mock client."""
    from custom_components.norman_shutters.coordinator import NormanCoordinator

    coordinator = NormanCoordinator(
        fake_hass, "192.168.1.100", mac_address="AABBCCDDEEFF", config_entry=MagicMock()
    )
    coordinator.client = MagicMock()
    coordinator.async_request_refresh = AsyncMock()
    coordinator.async_request_aggressive_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def config_flow(fake_hass):
    """NormanShuttersConfigFlow with hass and context pre-set."""
    from custom_components.norman_shutters.config_flow import NormanShuttersConfigFlow

    flow = NormanShuttersConfigFlow()
    flow.hass = fake_hass
    # NormanShuttersConfigFlow.__init__ doesn't call super().__init__(), so
    # self.context is not set automatically — set it here for zeroconf tests.
    flow.context = {}
    return flow
