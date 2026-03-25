"""Time platform for Growatt Modbus Integration."""
import logging
from datetime import time as dt_time
from typing import Any

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, WRITABLE_REGISTERS, CONF_REGISTER_MAP, get_device_type_for_control
from .coordinator import GrowattModbusCoordinator

_LOGGER = logging.getLogger(__name__)

# Controls that use hex-packed time encoding: register_value = hours*256 + minutes
# e.g. 06:00 = 0x0600 = 1536, 22:00 = 0x1600 = 5632
TIME_CONTROLS = {k for k in WRITABLE_REGISTERS if 'time_period' in k and k.endswith(('_start', '_end'))}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Growatt Modbus time entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    register_map_name = config_entry.data.get(CONF_REGISTER_MAP)
    from .const import REGISTER_MAPS
    holding_registers = REGISTER_MAPS.get(register_map_name, {}).get('holding_registers', {})

    entities = []
    for control_name in sorted(TIME_CONTROLS):  # sorted for deterministic order
        control_config = WRITABLE_REGISTERS[control_name]
        if control_config['register'] not in holding_registers:
            continue
        entities.append(GrowattGenericTime(coordinator, config_entry, control_name, control_config))
        _LOGGER.info("%s time control enabled (register %d)", control_name, control_config['register'])

    if entities:
        _LOGGER.info("Created %d time entities for %s", len(entities), config_entry.data['name'])
        async_add_entities(entities)


class GrowattGenericTime(CoordinatorEntity, TimeEntity):
    """Time entity for inverter time period start/end controls.

    Hardware stores time as hex-packed bytes: hours*256 + minutes.
    e.g. 06:00 = 0x0600 = 1536, 22:00 = 0x1600 = 5632.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:clock-outline"

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
        control_name: str,
        control_config: dict,
    ) -> None:
        """Initialize the time entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._control_name = control_name
        self._control_config = control_config

        friendly_name = control_name.replace('_', ' ').title()
        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} {friendly_name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{control_name}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.get_device_info(get_device_type_for_control(self._control_name))

    @property
    def native_value(self) -> dt_time | None:
        """Return the current time value decoded from hex-packed register."""
        data = self.coordinator.data
        if data is None:
            return None
        raw = getattr(data, self._control_name, None)
        if raw is None:
            return None
        hours = (int(raw) >> 8) & 0xFF
        minutes = int(raw) & 0xFF
        try:
            return dt_time(hours, minutes)
        except ValueError:
            _LOGGER.warning(
                "Invalid packed time value 0x%04X (%d) for %s — hours=%d, minutes=%d",
                int(raw), int(raw), self._control_name, hours, minutes,
            )
            return None

    async def async_set_value(self, value: dt_time) -> None:
        """Write a new time value encoded as hex-packed bytes to the Modbus register."""
        raw_value = (value.hour << 8) | value.minute
        register = self._control_config['register']
        success = await self.hass.async_add_executor_job(
            self.coordinator.modbus_client.write_register, register, raw_value
        )
        if success:
            _LOGGER.info(
                "Set %s to %s (raw=0x%04X=%d)",
                self._control_name, value.strftime("%H:%M"), raw_value, raw_value,
            )
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to write %s (register %d)", self._control_name, register)
