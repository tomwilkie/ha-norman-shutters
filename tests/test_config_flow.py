from ipaddress import IPv4Address
from unittest.mock import MagicMock

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from pytest_homeassistant.common import MockConfigEntry

from custom_components.norman_shutters.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


def make_discovery(name: str, host: str) -> ZeroconfServiceInfo:
    return ZeroconfServiceInfo(
        ip_address=IPv4Address(host),
        ip_addresses=[IPv4Address(host)],
        hostname=name.split(".")[0] + ".local.",
        name=name,
        port=80,
        type="_http._tcp.local.",
        properties={},
    )


async def _zeroconf(hass: HomeAssistant, name: str, host: str = "192.168.1.10"):
    return await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=make_discovery(name, host),
    )


# ---------------------------------------------------------------------------
# Zeroconf discovery
# ---------------------------------------------------------------------------


async def test_zeroconf_shows_confirm_form(hass: HomeAssistant, mock_login: MagicMock) -> None:
    result = await _zeroconf(hass, "NORMANHUB_9DDAA3._http._tcp.local.")

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"
    assert result["description_placeholders"] == {"host": "192.168.1.10"}


async def test_zeroconf_confirm_creates_entry_with_mac(
    hass: HomeAssistant, mock_login: MagicMock
) -> None:
    """Norman OUI + 6-char service name suffix reconstructs the full MAC."""
    result = await _zeroconf(hass, "NORMANHUB_9DDAA3._http._tcp.local.")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: "192.168.1.10", CONF_MAC: "805E4F9DDAA3"}
    assert result["result"].unique_id == "805E4F9DDAA3"


async def test_zeroconf_falls_back_to_ip_when_suffix_not_hex(
    hass: HomeAssistant, mock_login: MagicMock
) -> None:
    result = await _zeroconf(hass, "NORMANHUB_ZZZZZZ._http._tcp.local.")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: "192.168.1.10"}
    assert result["result"].unique_id == "192.168.1.10"


async def test_zeroconf_already_configured_updates_host(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.5", CONF_MAC: "805E4F9DDAA3"},
        unique_id="805E4F9DDAA3",
    )
    entry.add_to_hass(hass)

    result = await _zeroconf(hass, "NORMANHUB_9DDAA3._http._tcp.local.", "192.168.1.10")

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == "192.168.1.10"


# ---------------------------------------------------------------------------
# Manual (user) setup
# ---------------------------------------------------------------------------


async def test_user_step_shows_form(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_user_step_connection_failure(hass: HomeAssistant, mock_login: MagicMock) -> None:
    mock_login.side_effect = OSError("cannot connect")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_step_success(hass: HomeAssistant, mock_login: MagicMock) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.100"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Norman Hub (192.168.1.100)"
    assert result["data"] == {CONF_HOST: "192.168.1.100"}
    mock_login.assert_called_with("192.168.1.100")


# ---------------------------------------------------------------------------
# Options flow
# ---------------------------------------------------------------------------


async def test_options_flow_defaults_and_saves(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    result = await hass.config_entries.options.async_init(init_integration.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    default = next(k for k in schema if k == CONF_SCAN_INTERVAL).default()
    assert default == DEFAULT_SCAN_INTERVAL

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 120}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert init_integration.options == {CONF_SCAN_INTERVAL: 120}


async def test_options_flow_uses_existing_interval(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    hass.config_entries.async_update_entry(init_integration, options={CONF_SCAN_INTERVAL: 180})
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(init_integration.entry_id)
    schema = result["data_schema"].schema

    assert next(k for k in schema if k == CONF_SCAN_INTERVAL).default() == 180
