"""SMA Solar Webconnect interface."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.restore_state import ExtraStoredData
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.restore_state import RestoreEntity
from . import MY_KEY
from .dataupdater import timeframeStatus

SENSOR_ENTITIES: dict[str, SensorEntityDescription] = {}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SMA sensors."""
    myId = f'{int(config_entry.data["id"]):012}'
    data = hass.data[MY_KEY]

    entityDescription = SensorEntityDescription(
        name="Status",
        key="status",
    )
    sensordata = data.sendata[myId]
    #    config = sensordata.configdata

    entities = SMASempSensosr(
        data.coordinator,
        myId + "-status",
        entityDescription,
        sensordata.device_info,
    )
    sensordata.sensors_status = entities
    async_add_entities([entities])


class SMASempSensorExtraStoredData(
    ExtraStoredData
):  # pylint: disable=too-few-public-methods
    """Storage-Class for RestoreEntity"""

    def __init__(self, data: dict[str, Any]):
        self._data = data

    def as_dict(self) -> dict[str, Any]:
        return self._data


class SMASempSensosr(CoordinatorEntity, SensorEntity, RestoreEntity):
    """Representation of a SMA sensor."""

    _value: str
    _sempstatus: str = ""
    _entitystatus: str = ""
    _deviceid: str = ""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        coordinator: DataUpdateCoordinator,
        config_entry_unique_id: str,
        description: SensorEntityDescription | None,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._value = "Not connected"
        assert description is not None
        self.entity_description = description
        self._attr_device_info = device_info
        self._attr_unique_id = f"{config_entry_unique_id}-status"
        self._attr_extra_state_attributes: Dict[str, Any] = {}

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass."""
        last_extra = await self.async_get_last_extra_data()
        self._value = ""
        if last_extra:
            self._attr_extra_state_attributes = last_extra.as_dict()
            if self._attr_extra_state_attributes["currentTimeframe"]:
                tf = self._attr_extra_state_attributes["currentTimeframe"]
                self._attr_extra_state_attributes["currentTimeframe"] = (
                    timeframeStatus(
                        tf["active"],
                        tf["currentTimeframe"],
                        tf["activeCounter"],
                        datetime.fromisoformat(tf["currentTime"]),
                    )
                    if tf["currentTime"]
                    else None
                )
        await super().async_added_to_hass()

    @property
    def name(self) -> str:
        """Return the name of the sensor prefixed with the device name."""
        if self._attr_device_info is None or not (
            name_prefix := self._attr_device_info.get("name")
        ):
            name_prefix = "SMA"

        return f"{name_prefix} {super().name}"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self._value

    def set_value(self, value: str, additionalAttributes: Dict):
        """Set the value and the additional Attributes for this sensor"""
        self._value = value
        self._attr_extra_state_attributes = additionalAttributes
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        await super().async_will_remove_from_hass()

    @property
    def extra_restore_state_data(self) -> ExtraStoredData | None:
        if self._attr_extra_state_attributes is None:
            return None

        return SMASempSensorExtraStoredData(self._attr_extra_state_attributes)
