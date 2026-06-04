from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NUM_UNITS, CONF_UNIT_MODELS, DOMAIN, DRYER_STATUS_DRYING
from .coordinator import AceDryerCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AceDryerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AceDryerRunningSensor(coordinator, entry, unit_id)
        for unit_id in range(entry.data[CONF_NUM_UNITS])
    )


class AceDryerRunningSensor(CoordinatorEntity[AceDryerCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator: AceDryerCoordinator,
        entry: ConfigEntry,
        unit_id: int,
    ) -> None:
        super().__init__(coordinator)
        self._unit_id = unit_id
        self._attr_unique_id = f"{entry.entry_id}_unit{unit_id}_running"

        from .const import ACE_MODELS
        model_key = entry.data[CONF_UNIT_MODELS][unit_id]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_unit{unit_id}")},
            name=f"{coordinator.unit_name(unit_id)} Dryer",
            manufacturer="Anycubic",
            model=ACE_MODELS[model_key][0],
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.unit_dryer_status(self._unit_id) == DRYER_STATUS_DRYING
