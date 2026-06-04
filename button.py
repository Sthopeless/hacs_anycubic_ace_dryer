from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ACE_MODELS, CONF_NUM_UNITS, CONF_UNIT_MODELS, DOMAIN
from .coordinator import AceDryerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AceDryerCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = []
    for unit_id in range(entry.data[CONF_NUM_UNITS]):
        entities.extend([
            AceDryerStartButton(coordinator, entry, unit_id),
            AceDryerStopButton(coordinator, entry, unit_id),
        ])
    async_add_entities(entities)


def _device_info(coordinator: AceDryerCoordinator, entry: ConfigEntry, unit_id: int) -> DeviceInfo:
    model_key = entry.data[CONF_UNIT_MODELS][unit_id]
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_unit{unit_id}")},
        name=f"{coordinator.unit_name(unit_id)} Dryer",
        manufacturer="Anycubic",
        model=ACE_MODELS[model_key][0],
    )


class _AceDryerButton(CoordinatorEntity[AceDryerCoordinator], ButtonEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AceDryerCoordinator,
        entry: ConfigEntry,
        unit_id: int,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._unit_id = unit_id
        self._attr_unique_id = f"{entry.entry_id}_unit{unit_id}_{key}"
        self._attr_device_info = _device_info(coordinator, entry, unit_id)


class AceDryerStartButton(_AceDryerButton):
    _attr_name = "Start Drying"
    _attr_icon = "mdi:heat-wave"

    def __init__(self, coordinator, entry, unit_id):
        super().__init__(coordinator, entry, unit_id, "start")

    async def async_press(self) -> None:
        settings = self.coordinator.desired[self._unit_id]
        try:
            await self.coordinator.api.start_drying(
                unit_id=self._unit_id,
                temp=settings["temp"],
                duration=settings["duration"],
                fan_speed=settings["fan_speed"],
            )
        except Exception as err:
            _LOGGER.error("Failed to start dryer on unit %d: %s", self._unit_id, err)
            return
        await self.coordinator.async_request_refresh()


class AceDryerStopButton(_AceDryerButton):
    _attr_name = "Stop Drying"
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, coordinator, entry, unit_id):
        super().__init__(coordinator, entry, unit_id, "stop")

    async def async_press(self) -> None:
        try:
            await self.coordinator.api.stop_drying(unit_id=self._unit_id)
        except Exception as err:
            _LOGGER.error("Failed to stop dryer on unit %d: %s", self._unit_id, err)
            return
        await self.coordinator.async_request_refresh()
