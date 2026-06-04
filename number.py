from __future__ import annotations

import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ACE_MODELS, CONF_NUM_UNITS, CONF_UNIT_MODELS, DOMAIN
from .coordinator import AceDryerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AceDryerCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[NumberEntity] = []
    for unit_id in range(entry.data[CONF_NUM_UNITS]):
        model_key = entry.data[CONF_UNIT_MODELS][unit_id]
        _, temp_min, temp_max = ACE_MODELS[model_key]
        entities.extend([
            AceDryerTemperatureNumber(coordinator, entry, unit_id, temp_min, temp_max),
            AceDryerDurationNumber(coordinator, entry, unit_id),
            AceDryerFanSpeedNumber(coordinator, entry, unit_id),
        ])
    async_add_entities(entities, update_before_add=True)


def _device_info(coordinator: AceDryerCoordinator, entry: ConfigEntry, unit_id: int) -> DeviceInfo:
    model_key = entry.data[CONF_UNIT_MODELS][unit_id]
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_unit{unit_id}")},
        name=f"{coordinator.unit_name(unit_id)} Dryer",
        manufacturer="Anycubic",
        model=ACE_MODELS[model_key][0],
    )


class _AceDryerNumber(CoordinatorEntity[AceDryerCoordinator], NumberEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        coordinator: AceDryerCoordinator,
        entry: ConfigEntry,
        unit_id: int,
        key: str,
        default: int,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        self._unit_id = unit_id
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_unit{unit_id}_{key}"
        self._attr_device_info = _device_info(coordinator, entry, unit_id)
        coordinator.desired[unit_id].setdefault(key, default)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in ("unavailable", "unknown", None):
            try:
                self.coordinator.desired[self._unit_id][self._key] = int(float(last.state))
            except ValueError:
                pass

    @property
    def native_value(self) -> float:
        return float(self.coordinator.desired[self._unit_id][self._key])

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.desired[self._unit_id][self._key] = int(value)
        self.async_write_ha_state()


class AceDryerTemperatureNumber(_AceDryerNumber):
    _attr_name = "Temperature"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_native_step = 5
    _attr_icon = "mdi:thermometer"

    def __init__(self, coordinator, entry, unit_id, temp_min, temp_max):
        default = min(45, temp_max)
        super().__init__(coordinator, entry, unit_id, "temp", default)
        self._attr_native_min_value = float(temp_min)
        self._attr_native_max_value = float(temp_max)
        coordinator.desired[unit_id]["temp"] = default


class AceDryerDurationNumber(_AceDryerNumber):
    _attr_name = "Duration"
    _attr_native_unit_of_measurement = "min"
    _attr_native_min_value = 10.0
    _attr_native_max_value = 480.0
    _attr_native_step = 10.0
    _attr_icon = "mdi:timer-outline"

    def __init__(self, coordinator, entry, unit_id):
        super().__init__(coordinator, entry, unit_id, "duration", 120)


class AceDryerFanSpeedNumber(_AceDryerNumber):
    _attr_name = "Fan Speed"
    _attr_native_unit_of_measurement = "RPM"
    _attr_native_min_value = 0.0
    _attr_native_max_value = 5000.0
    _attr_native_step = 100.0
    _attr_icon = "mdi:fan"

    def __init__(self, coordinator, entry, unit_id):
        super().__init__(coordinator, entry, unit_id, "fan_speed", 0)
