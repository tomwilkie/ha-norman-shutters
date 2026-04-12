import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pynormanshutters import login

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class NormanCoordinator(DataUpdateCoordinator):
    """Coordinator for Norman Shutters - polls get_window_info every 30s."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.host = host
        self.client = None

    async def _async_setup(self) -> None:
        """Login to the hub. Called once during config entry setup."""
        self.client = await self.hass.async_add_executor_job(login, self.host)

    async def _async_update_data(self) -> dict[str, dict]:
        """Fetch window state from the hub, re-logging in on session expiry."""
        try:
            raw = await self.hass.async_add_executor_job(self.client.get_window_info)
        except Exception as err:
            _LOGGER.debug("get_window_info failed (%s), attempting re-login", err)
            try:
                await self._async_setup()
                raw = await self.hass.async_add_executor_job(self.client.get_window_info)
            except Exception as err2:
                raise UpdateFailed(f"Error communicating with Norman Hub: {err2}") from err2

        return self._parse_window_info(raw)

    @staticmethod
    def _parse_window_info(raw: dict) -> dict[str, dict]:
        """Parse get_window_info() response into a dict keyed by window Id.

        Actual API response shape:
          {
            "totalWindow": 6,
            "windows": [
              {
                "Id":       52280,   # unique integer ID for this shutter
                "Name":     "Right Window 1",
                "position": 37,      # travel position, 0-100
                "angle":    0,       # slat tilt, 0-100
                "battery":  "57",    # battery percentage as a string
                "solar":    245,     # solar charge level (mW)
                "Rssi":     67,      # signal strength
                "temp":     17,      # temperature (°C)
                ...
              }
            ]
          }
        """
        return {str(w["Id"]): w for w in raw.get("windows", [])}
