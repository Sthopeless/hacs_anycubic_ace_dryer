from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NUM_UNITS, CONF_UNIT_MODELS, DOMAIN, STATUS_LABELS
from .coordinator import AceDryerCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AceDryerCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for unit_id in range(entry.data[CONF_NUM_UNITS]):
        entities.extend([
            AceDryerStatusSensor(coordinator, entry, unit_id),
            AceDryerTargetTempSensor(coordinator, entry, unit_id),
        ])
    async_add_entities(entities)


def _device_info(coordinator: AceDryerCoordinator, entry: ConfigEntry, unit_id: int) -> DeviceInfo:
    model_key = entry.data[CONF_UNIT_MODELS][unit_id]
    from .const import ACE_MODELS
    model_name = ACE_MODELS[model_key][0]
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_unit{unit_id}")},
        name=f"{coordinator.unit_name(unit_id)} Dryer",
        manufacturer="Anycubic",
        model=model_name,
    )


class _AceDryerSensor(CoordinatorEntity[AceDryerCoordinator], SensorEntity):
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


class AceDryerStatusSensor(_AceDryerSensor):
    _attr_name = "Status"
    _attr_icon = "mdi:tumble-dryer"

    def __init__(self, coordinator, entry, unit_id):
        super().__init__(coordinator, entry, unit_id, "status")

    @property
    def native_value(self) -> str:
        raw = self.coordinator.unit_dryer_status(self._unit_id)
        return STATUS_LABELS.get(raw, raw)

    @property
    def extra_state_attributes(self) -> dict:
        return {"raw_status": self.coordinator.unit_dryer_status(self._unit_id)}


class AceDryerTargetTempSensor(_AceDryerSensor):
    _attr_name = "Target Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, coordinator, entry, unit_id):
        super().__init__(coordinator, entry, unit_id, "target_temp")

    @property
    def native_value(self) -> int:
        return self.coordinator.unit_dryer_target_temp(self._unit_id)
