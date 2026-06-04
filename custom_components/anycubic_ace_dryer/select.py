from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ACE_MODELS, CONF_NUM_UNITS, CONF_UNIT_MODELS, DOMAIN, MATERIAL_PRESETS
from .coordinator import AceDryerCoordinator

_TEMP_TO_PRESET = {v: k for k, v in MATERIAL_PRESETS.items() if v is not None}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: AceDryerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        AceDryerMaterialSelect(coordinator, entry, unit_id)
        for unit_id in range(entry.data[CONF_NUM_UNITS])
    )


class AceDryerMaterialSelect(
    CoordinatorEntity[AceDryerCoordinator], SelectEntity, RestoreEntity
):
    _attr_has_entity_name = True
    _attr_name = "Material Preset"
    _attr_icon = "mdi:filament"
    _attr_options = list(MATERIAL_PRESETS.keys())

    def __init__(
        self,
        coordinator: AceDryerCoordinator,
        entry: ConfigEntry,
        unit_id: int,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        self._unit_id = unit_id
        self._attr_unique_id = f"{entry.entry_id}_unit{unit_id}_material"
        model_key = entry.data[CONF_UNIT_MODELS][unit_id]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_unit{unit_id}")},
            name=f"{coordinator.unit_name(unit_id)} Dryer",
            manufacturer="Anycubic",
            model=ACE_MODELS[model_key][0],
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in self._attr_options:
            temp = MATERIAL_PRESETS.get(last.state)
            if temp is not None:
                self.coordinator.desired[self._unit_id]["temp"] = temp

    @property
    def current_option(self) -> str:
        current_temp = self.coordinator.desired[self._unit_id]["temp"]
        return _TEMP_TO_PRESET.get(current_temp, "Custom")

    async def async_select_option(self, option: str) -> None:
        temp = MATERIAL_PRESETS.get(option)
        if temp is not None:
            self.coordinator.desired[self._unit_id]["temp"] = temp
        self.async_write_ha_state()
