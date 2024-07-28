"""Tracks the latency of a host by sending ICMP echo requests (ping)."""

from __future__ import annotations

import logging
from typing import Any, List

from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.const import STATE_ON


from . import MY_KEY

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    #    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup Switch Entity"""
    myId = f'{int(config_entry.data["id"]):12}'
    data = hass.data[MY_KEY]
    sensordata = data.sendata[myId]
    config = sensordata.configdata
    _LOGGER.info(f"Switch Setup {config}")
    sensors: List[SempSwitch] = []
    if config.onoffswitch is not None:
        sed = SwitchEntityDescription(
            name="is controlled",
            key="timecontrol",
            entity_registry_enabled_default=True,
            entity_category=EntityCategory.CONFIG,
            device_class=SwitchDeviceClass.SWITCH,
        )

        s = SempSwitch(
            data.coordinator,
            myId + "-controlled",
            sed,
            sensordata.device_info,
        )
        sensordata.switch_controllable = s
        sensors.append(s)

    if config.minontime is not None:
        sed = SwitchEntityDescription(
            name="is interruptable",
            key="interruptable",
            entity_registry_enabled_default=True,
            entity_category=EntityCategory.CONFIG,
            device_class=SwitchDeviceClass.SWITCH,
        )

        s = SempSwitch(
            data.coordinator,
            myId + "-interruptable",
            sed,
            sensordata.device_info,
        )
        sensordata.switch_interruptable = s
        sensors.append(s)

    _LOGGER.error(f"sensors {sensors}")
    _LOGGER.error(f"sensordata {sensordata}")
    if sensors:
        _LOGGER.error(f"Adding sensors {sensors}")
        async_add_entities(sensors)


class SempSwitch(CoordinatorEntity, SwitchEntity, RestoreEntity):
    """A class to let you turn functionality on Roborock devices on
    and off that does need a coordinator."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry_unique_id: str,
        description: SwitchEntityDescription,
        device_info: DeviceInfo,
        #        config_data: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        assert description is not None
        self.entity_description = description
        # self._attr_name = f"{config_entry_unique_id}-allowcontrol"
        self._attr_device_info = device_info
        self._attr_unique_id = f"{config_entry_unique_id}-allowcontrol"
        self._value = True

    #        self._attr_unique_id = f"{config_entry_unique_id}-status"

    @property
    def name(self) -> str:
        """Return the name of the sensor prefixed with the device name."""
        if self._attr_device_info is None or not (
            name_prefix := self._attr_device_info.get("name")
        ):
            name_prefix = "SMA"

        return f"{name_prefix} {super().name}"

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass."""
        last_state = await self.async_get_last_state()
        if last_state is None or last_state.state == STATE_ON:
            await self.async_turn_on()
        else:
            await self.async_turn_off()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        self._value = False
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        self._value = True
        self.async_write_ha_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        self._value = False
        self.async_write_ha_state()

    def turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        self._value = True
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self._value
