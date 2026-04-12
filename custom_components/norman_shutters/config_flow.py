from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.zeroconf import ZeroconfServiceInfo
from homeassistant.data_entry_flow import FlowResult
from pynormanshutters.main import login

from .const import CONF_HOST, DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_NAME_PREFIX = "NORMANHUB_"


class NormanShuttersConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Norman Shutters."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._unique_id: str | None = None

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
        self._host = discovery_info.host

        # Service name format: "NORMANHUB_AABBCCDDEEFF._http._tcp.local."
        # Extract the MAC to use as a stable unique ID (survives DHCP changes).
        raw_name = discovery_info.name  # e.g. "NORMANHUB_AABBCC._http._tcp.local."
        hub_label = raw_name.split(".")[0]  # "NORMANHUB_AABBCC"
        self._unique_id = hub_label.removeprefix(SERVICE_NAME_PREFIX) or self._host

        await self.async_set_unique_id(self._unique_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: self._host})

        self.context["title_placeholders"] = {"host": self._host}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm addition of a discovered hub."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Norman Hub ({self._host})",
                data={CONF_HOST: self._host},
            )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"host": self._host},
        )
