"""Constants for the SMA Semp integration."""

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any
import typing
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import Platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util.hass_dict import HassKey
from pysmaplus.semp import semp

# from pysmaplus.device import
from pysmaplus.semp.device import sempTimeframe, sempDevice
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "smasemp"
CONF_SOURCE_SENSOR = "source"
CONF_DEVICE_TYP = "semptyp"
CONF_SOURCE_MAXCONSUMPTION = "sempmaxconsumption"
CONF_SOURCE_MINCONSUMPTION = "sempminconsumption"
CONF_TIMECONTROLL = "timecontroll"
CONF_INTERRUPTIONS_ALLOWED = "interruptionsallowed"
CONF_CALENDAR = "calendar"
CONF_CONTROLLTYPE = "controlltype"
CONF_MINONTIME = "minontime"
# CONF_MAXONTIME = "maxontime"
CONF_MINOFFTIME = "minofftime"
# CONF_MAXOFFTIME = "maxofftime"
CONF_MINRUNNINGTIME = "minrunningtime"
CONF_MAXRUNNINGTIME = "maxrunningtime"
CONF_ONOFFSWITCH = "onoffswitch"
CONF_PREFIX = "prefix"

PORT = 13673
SMASEMP_COORDINATOR = "coordinator"
SEMASEMP_OBJECT = "smasma"
SMASEMP_REMOVE_LISTENER = "remove_listener"
PLATFORMS = [Platform.SENSOR, Platform.SWITCH]

DEFAULT_SCAN_INTERVAL = 5

ATTR_SEMPSTATUS = "sempstatus"
ATTR_ENTITY = "entitystatus"
ATTR_DEVICEID = "deviceid"

MY_KEY: HassKey["SempIntegrationData"] = HassKey(DOMAIN)
from dacite import from_dict


@dataclass
class sensor_configuration:
    """Structure for Config-Entries"""

    # Only Reporting
    name: str
    source: str
    semptyp: str
    id: float
    sempmaxconsumption: float | None

    # Controllable
    sempminconsumption: float | None
    minrunningtime: dict | None
    maxrunningtime: dict | None
    calendar: str | None
    onoffswitch: str | None

    # Interruptable
    minontime: dict | None
    minofftime: dict | None

    # Conditions
    controllable: bool = False
    interruptable: bool = False

    prefix: str | None = "11223344"

    @staticmethod
    def from_dict(values: MappingProxyType[str, Any]):
        v = values.copy()
        if "prefix" in v and isinstance(v["prefix"], float):
            v["prefix"] = str(int(v["prefix"]))
        c = from_dict(sensor_configuration, v)
        c.controllable = c.onoffswitch is not None
        c.interruptable = c.minontime is not None and c.minofftime is not None
        return c


@dataclass
class SempDeviceInfo:
    """Semp-Informationen for one device"""

    id: str
    device_info: DeviceInfo
    unique_id: str | None
    configdata: sensor_configuration
    device: sempDevice = None
    sensors_status: Any | None = None
    switch_controllable: SwitchEntity | None = None
    switch_interruptable: SwitchEntity | None = None
    timeframes: list[sempTimeframe] = field(default_factory=list)
    history: list[dict] = field(default_factory=list)
    last_start: None | datetime = None
    running_time: int = 0


@dataclass
class SempIntegrationData:
    """Datastructure for this integration"""

    sempserver: semp
    coordinator: DataUpdateCoordinator
    ip: str
    port: int
    sendata: dict[str, SempDeviceInfo]
