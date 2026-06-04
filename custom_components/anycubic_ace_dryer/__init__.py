from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import AceDryerAPI
from .const import CONF_HOST, CONF_NUM_UNITS, DOMAIN, MOONRAKER_PORT
from .coordinator import AceDryerCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "number", "select", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = AceDryerAPI(entry.data[CONF_HOST], MOONRAKER_PORT)
    coordinator = AceDryerCoordinator(hass, api, entry.data[CONF_NUM_UNITS])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: AceDryerCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.close()
    return unload_ok
