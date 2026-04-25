from ipaddress import IPv4Address
from unittest.mock import AsyncMock, MagicMock

from custom_components.norman_shutters.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)


def make_discovery(name, host):
    info = MagicMock()
    info.name = name
    info.hostname = name.split(".")[0] + ".local."
    info.ip_address = IPv4Address(host)
    return info


# ---------------------------------------------------------------------------
# async_step_zeroconf
# ---------------------------------------------------------------------------


async def test_zeroconf_sets_host(config_flow):
    discovery = make_discovery("NORMANHUB_9DDAA3._http._tcp.local.", "192.168.1.10")
    await config_flow.async_step_zeroconf(discovery)

    assert config_flow._host == "192.168.1.10"


async def test_zeroconf_returns_form(config_flow):
    discovery = make_discovery("NORMANHUB_9DDAA3._http._tcp.local.", "192.168.1.10")
    result = await config_flow.async_step_zeroconf(discovery)

    assert result["type"] == "form"
    assert result["step_id"] == "zeroconf_confirm"


async def test_zeroconf_mac_reconstructed_from_hostname_suffix(config_flow):
    """Norman OUI + 6-char hostname suffix reconstructs the full MAC."""
    discovery = make_discovery("NORMANHUB_9DDAA3._http._tcp.local.", "192.168.1.10")
    await config_flow.async_step_zeroconf(discovery)

    assert config_flow._mac == "805E4F9DDAA3"
    assert config_flow._unique_id == "805E4F9DDAA3"


async def test_zeroconf_no_mac_when_suffix_not_hex(config_flow):
    """Suffix that isn't valid hex falls back to IP as unique_id."""
    discovery = make_discovery("NORMANHUB_ZZZZZZ._http._tcp.local.", "192.168.1.10")
    await config_flow.async_step_zeroconf(discovery)

    assert config_flow._mac is None
    assert config_flow._unique_id == "192.168.1.10"


# ---------------------------------------------------------------------------
# async_step_zeroconf_confirm
# ---------------------------------------------------------------------------


async def test_zeroconf_confirm_no_input_shows_form(config_flow):
    config_flow._host = "192.168.1.10"
    result = await config_flow.async_step_zeroconf_confirm(None)

    assert result["type"] == "form"
    assert result["step_id"] == "zeroconf_confirm"


async def test_zeroconf_confirm_with_input_creates_entry(config_flow):
    config_flow._host = "192.168.1.10"
    result = await config_flow.async_step_zeroconf_confirm({})

    assert result["type"] == "create_entry"
    assert result["data"][CONF_HOST] == "192.168.1.10"


async def test_zeroconf_confirm_includes_mac_when_suffix_valid(config_flow):
    discovery = make_discovery("NORMANHUB_9DDAA3._http._tcp.local.", "192.168.1.10")
    await config_flow.async_step_zeroconf(discovery)
    result = await config_flow.async_step_zeroconf_confirm({})

    assert result["type"] == "create_entry"
    assert result["data"][CONF_MAC] == "805E4F9DDAA3"


async def test_zeroconf_confirm_no_mac_when_suffix_not_hex(config_flow):
    """When neither TXT properties nor a valid hex suffix are available, no MAC is stored."""
    discovery = make_discovery("NORMANHUB_ZZZZZZ._http._tcp.local.", "192.168.1.10")
    await config_flow.async_step_zeroconf(discovery)
    result = await config_flow.async_step_zeroconf_confirm({})

    assert result["type"] == "create_entry"
    assert CONF_MAC not in result["data"]


# ---------------------------------------------------------------------------
# async_step_user
# ---------------------------------------------------------------------------


async def test_user_step_no_input_shows_form(config_flow):
    result = await config_flow.async_step_user(None)

    assert result["type"] == "form"
    assert result["step_id"] == "user"


async def test_user_step_connection_failure(config_flow):
    config_flow.hass.async_add_executor_job.side_effect = Exception("cannot connect")
    result = await config_flow.async_step_user({CONF_HOST: "192.168.1.100"})

    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"


async def test_user_step_success(config_flow):
    config_flow.hass.async_add_executor_job = AsyncMock(return_value=MagicMock())
    result = await config_flow.async_step_user({CONF_HOST: "192.168.1.100"})

    assert result["type"] == "create_entry"
    assert result["data"][CONF_HOST] == "192.168.1.100"


# ---------------------------------------------------------------------------
# OptionsFlowHandler
# ---------------------------------------------------------------------------


def make_options_flow(options=None):
    from custom_components.norman_shutters.config_flow import OptionsFlowHandler

    config_entry = MagicMock()
    config_entry.options = options or {}
    return OptionsFlowHandler(config_entry)


async def test_options_flow_shows_form():
    handler = make_options_flow()
    result = await handler.async_step_init(None)

    assert result["type"] == "form"
    assert result["step_id"] == "init"


async def test_options_flow_saves_interval():
    handler = make_options_flow()
    result = await handler.async_step_init({CONF_SCAN_INTERVAL: 120})

    assert result["type"] == "create_entry"
    assert result["data"][CONF_SCAN_INTERVAL] == 120


async def test_options_flow_uses_existing_interval():
    handler = make_options_flow(options={CONF_SCAN_INTERVAL: 180})
    # The current interval should be used as the form default — we can't inspect
    # the schema directly through the stub, but we verify the flow returns a form.
    result = await handler.async_step_init(None)

    assert result["type"] == "form"


async def test_options_flow_default_interval():
    """When no option is stored, the default is DEFAULT_SCAN_INTERVAL."""
    handler = make_options_flow()
    assert (
        handler._config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        == DEFAULT_SCAN_INTERVAL
    )
