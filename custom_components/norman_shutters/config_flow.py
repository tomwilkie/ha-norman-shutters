from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from pynormanshutters import login

from .const import CONF_HOST, CONF_MAC, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Norman Hub devices share a common OUI. The mDNS hostname suffix (e.g.
# "9DDAA3" in "NORMANHUB_9DDAA3") is the last 3 bytes of the MAC address.
NORMAN_OUI = "805E4F"
SERVICE_NAME_PREFIX = "NORMANHUB_"


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Norman Shutters options (e.g. poll interval)."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                        int, vol.Range(min=5, max=3600)
                    )
                }
            ),
        )


class NormanShuttersConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Norman Shutters."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry) -> OptionsFlowHandler:
        return OptionsFlowHandler(config_entry)

    def __init__(self) -> None:
        self._host: str | None = None
        self._unique_id: str | None = None
        self._mac: str | None = None

    # ------------------------------------------------------------------
    # Manual setup (user-initiated from Integrations UI)
    # ------------------------------------------------------------------

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            try:
                await self.hass.async_add_executor_job(login, host)
            except Exception:
                _LOGGER.exception("Cannot connect to Norman Hub at %s", host)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Norman Hub ({host})",
                    data={CONF_HOST: host},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Zeroconf auto-discovery
    # ------------------------------------------------------------------

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> FlowResult:
        """Handle discovery of a Norman Hub via mDNS."""
        self._host = str(discovery_info.ip_address)

        _LOGGER.debug(
            "Norman Hub zeroconf discovery: name=%r hostname=%r",
            discovery_info.name,
            discovery_info.hostname,
        )

        # Reconstruct the full MAC from the service name suffix. Norman Hub devices
        # use a fixed OUI and embed the last 3 MAC bytes in the service name
        # (e.g. "NORMANHUB_9DDAA3" → full MAC "805E4F9DDAA3").
        mac_hex: str | None = None
        hub_label = discovery_info.name.split(".")[0]
        suffix = hub_label.removeprefix(SERVICE_NAME_PREFIX).upper()
        hex_chars = set("0123456789ABCDEF")
        if hub_label != suffix and len(suffix) == 6 and all(c in hex_chars for c in suffix):
            mac_hex = NORMAN_OUI + suffix

        self._mac = mac_hex
        self._unique_id = mac_hex or self._host

        await self.async_set_unique_id(self._unique_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: self._host})

        self.context["title_placeholders"] = {"host": self._host}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm addition of a discovered hub."""
        if user_input is not None:
            data: dict = {CONF_HOST: self._host}
            if self._mac:
                data[CONF_MAC] = self._mac
            return self.async_create_entry(
                title=f"Norman Hub ({self._host})",
                data=data,
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"host": self._host},
        )
