from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AceDryerAPI
from .const import DOMAIN, MATERIAL_PRESETS, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AceDryerCoordinator(DataUpdateCoordinator[dict]):
    def __init__(
        self,
        hass: HomeAssistant,
        api: AceDryerAPI,
        num_units: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )
        self.api = api
        self.num_units = num_units

        # Desired dryer settings per unit_id.
        # Number and Select entities write here; Start button reads from here.
        self.desired: dict[int, dict[str, int]] = {
            i: {"temp": 45, "duration": 120, "fan_speed": 0}
            for i in range(num_units)
        }

    def unit_name(self, unit_id: int) -> str:
        try:
            return self.data[f"unit_{unit_id}"]["name"] or f"ACE Unit {unit_id}"
        except (KeyError, TypeError):
            return f"ACE Unit {unit_id}"

    def unit_dryer_status(self, unit_id: int) -> str:
        try:
            return self.data[f"unit_{unit_id}"]["dryer_status"]
        except (KeyError, TypeError):
            return "stop"

    def unit_dryer_target_temp(self, unit_id: int) -> int:
        try:
            return int(self.data[f"unit_{unit_id}"]["dryer_target_temp"])
        except (KeyError, TypeError, ValueError):
            return 0

    async def _async_update_data(self) -> dict:
        try:
            return await self.api.get_mmu_machine()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Moonraker: {err}") from err
