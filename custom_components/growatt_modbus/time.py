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

from .const import DOMAIN, WRITABLE_REGISTERS, CONF_REGISTER_MAP, get_device_type_for_control, DEVICE_TYPE_BATTERY, MOD_TOU_PERIODS
from .coordinator import GrowattModbusCoordinator
from .growatt_modbus import ModbusWriteError

_LOGGER = logging.getLogger(__name__)

# Controls that use hex-packed time encoding: register_value = hours*256 + minutes
# e.g. 06:00 = 0x0600 = 1536, 22:00 = 0x1600 = 5632
TIME_CONTROLS = {k for k in WRITABLE_REGISTERS if 'time_period' in k and k.endswith(('_start', '_end'))}

# MOD_TOU_PERIODS is defined in const.py and imported above


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

    # MOD TL3-XH TOU time pickers (4 start + 4 end = 8 entities)
    if 3038 in holding_registers:
        for period_def in MOD_TOU_PERIODS:
            p = period_def["period"]
            entities.append(GrowattModTouTime(coordinator, config_entry, period_def, is_start=True))
            entities.append(GrowattModTouTime(coordinator, config_entry, period_def, is_start=False))
        _LOGGER.info("MOD TOU time controls enabled (8 time entities for 4 periods)")

    if entities:
        _LOGGER.info("Created %d time entities for %s", len(entities), config_entry.data['name'])
        async_add_entities(entities)


class GrowattGenericTime(CoordinatorEntity, TimeEntity):
    """Time entity for inverter time period start/end controls.

    Hardware stores time as hex-packed bytes: hours*256 + minutes.
    e.g. 06:00 = 0x0600 = 1536, 22:00 = 0x1600 = 5632.
    """

    _attr_has_entity_name = True
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
        self._attr_name = friendly_name
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
        try:
            write_ok, verified = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register_verified, register, raw_value,
            )
        except ModbusWriteError:
            _LOGGER.error("Failed to write %s (register %d)", self._control_name, register)
            return
        if write_ok:
            if verified:
                _LOGGER.info(
                    "Set %s to %s (raw=0x%04X=%d, verified)",
                    self._control_name, value.strftime("%H:%M"), raw_value, raw_value,
                )
            else:
                _LOGGER.warning(
                    "%s: write succeeded but value reverted (possible cloud override)",
                    self._control_name,
                )
            self.coordinator.track_write(register, raw_value, self._control_name)
            await self.coordinator.async_request_refresh()


class GrowattModTouTime(CoordinatorEntity, TimeEntity):
    """Time entity for MOD TL3-XH TOU period start/end registers.

    Start registers encode: bit15=enable, bit13-14=priority, bit8-12=hour, bit0-7=minute.
    End registers encode: bit8-12=hour, bit0-7=minute (plain hex-packed).

    Writing to a start register uses read-modify-write to preserve the priority/enable bits.
    Writing to an end register does a plain hex-packed write.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:clock-outline"

    def __init__(
        self,
        coordinator: GrowattModbusCoordinator,
        config_entry: ConfigEntry,
        period_def: dict,
        is_start: bool,
    ) -> None:
        """Initialize the MOD TOU time entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._period_def = period_def
        self._is_start = is_start
        self._period = period_def["period"]

        if is_start:
            self._register = period_def["start_reg"]
            self._data_field = period_def["start_field"]
            label = f"TOU Period {self._period} Start"
        else:
            self._register = period_def["end_reg"]
            self._data_field = period_def["end_field"]
            label = f"TOU Period {self._period} End"

        entry_name = config_entry.data.get("name", config_entry.title)
        self._attr_name = f"{entry_name} {label}"
        self._attr_unique_id = f"{config_entry.entry_id}_mod_tou_{self._period}_{'start' if is_start else 'end'}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.get_device_info(DEVICE_TYPE_BATTERY)

    @property
    def native_value(self) -> dt_time | None:
        """Return the current time value decoded from the packed register."""
        data = self.coordinator.data
        if data is None:
            return None
        raw = getattr(data, self._data_field, None)
        if raw is None:
            return None
        # For start registers: bits 8-12 = hour (5 bits, mask out priority/enable bits 13-15)
        # For end registers: bits 8-15 = hour (but upper 3 bits should be 0 for valid times)
        # Using & 0x1F safely extracts hours 0-23 for both register types
        hours = (int(raw) >> 8) & 0x1F
        minutes = int(raw) & 0xFF
        try:
            return dt_time(hours, minutes)
        except ValueError:
            _LOGGER.warning(
                "Invalid packed time 0x%04X for %s — hours=%d, minutes=%d",
                int(raw), self._data_field, hours, minutes,
            )
            return None

    async def async_set_value(self, value: dt_time) -> None:
        """Write time to the register, using read-modify-write for start registers."""
        if self._is_start:
            # Read-modify-write: preserve priority (bits 13-14) and enable (bit 15)
            data = self.coordinator.data
            current_raw = getattr(data, self._data_field, 0) if data else 0
            new_raw = (int(current_raw) & 0xE000) | ((value.hour << 8) | value.minute)
        else:
            # End register: plain hex-packed write
            new_raw = (value.hour << 8) | value.minute

        try:
            write_ok, verified = await self.hass.async_add_executor_job(
                self.coordinator.modbus_client.write_register_verified, self._register, new_raw,
            )
        except ModbusWriteError:
            _LOGGER.error(
                "Failed to write MOD TOU period %d %s (register %d)",
                self._period, "start" if self._is_start else "end", self._register,
            )
            return
        if write_ok:
            slot = "start" if self._is_start else "end"
            if verified:
                _LOGGER.info(
                    "Set MOD TOU period %d %s to %s (raw=0x%04X=%d, verified)",
                    self._period, slot, value.strftime("%H:%M"), new_raw, new_raw,
                )
            else:
                _LOGGER.warning(
                    "MOD TOU period %d %s: write succeeded but value reverted (possible cloud override)",
                    self._period, slot,
                )
            self.coordinator.track_write(self._register, new_raw, self._data_field)
            await self.coordinator.async_request_refresh()
